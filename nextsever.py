import json
import six
from collections import namedtuple, MutableMapping
from graphql import (
    graphql,
    GraphQLSchema
)


class SkipException(Exception):
    pass


class HttpQueryError(Exception):
    def __init__(self, status_code, message=None, is_graphql_error=False, headers=None):
        self.status_code = status_code
        self.message = message
        self.is_graphql_error = is_graphql_error
        self.headers = headers
        super(HttpQueryError, self).__init__(message)

    def __eq__(self, other):
        return (
            isinstance(other, HttpQueryError)
            and other.status_code == self.status_code
            and other.message == self.message
            and other.headers == self.headers
        )

    def __hash__(self):
        if self.headers:
            headers_hash = tuple(self.headers.items())
        else:
            headers_hash = None

        return hash((self.status_code, self.message, headers_hash))


GraphQLParams = namedtuple("GraphQLParams", "query,variables,operation_name")
GraphQLResponse = namedtuple("GraphQLResponse", "result,status_code")


def run_http_query(
    schema,  # type: GraphQLSchema
    request_method,  # type: str
    data,  # type: Union[Dict, List[Dict]]
    query_data=None,  # type: Optional[Dict]
    batch_enabled=False,  # type: bool
    catch=False,  # type: bool
    **execute_options  # type: Dict
):
    if request_method not in ("get", "post"):
        raise HttpQueryError(
            405,
            "GraphQL only supports GET and POST requests.",
            headers={"Allow": "GET, POST"},
        )
    if catch:
        catch_exc = (
            HttpQueryError
        )  # type: Union[Type[HttpQueryError], Type[SkipException]]
    else:
        catch_exc = SkipException
    is_batch = isinstance(data, list)

    is_get_request = request_method == "get"
    allow_only_query = is_get_request

    if not is_batch:
        if not isinstance(data, (dict, MutableMapping)):
            raise HttpQueryError(
                400, "GraphQL params should be a dict. Received {}.".format(
                    data)
            )
        data = [data]
    elif not batch_enabled:
        raise HttpQueryError(400, "Batch GraphQL requests are not enabled.")

    if not data:
        raise HttpQueryError(
            400, "Received an empty list in the batch request.")

    extra_data = {}  # type: Dict[str, Any]
    # If is a batch request, we don't consume the data from the query
    if not is_batch:
        extra_data = query_data or {}

    all_params = [get_graphql_params(entry, extra_data) for entry in data]

    responses = [
        get_response(schema, params, catch_exc,
                     allow_only_query, **execute_options)
        for params in all_params
    ]

    return responses, all_params


def get_graphql_params(data, query_data):
    # type: (Dict, Dict) -> GraphQLParams
    query = data.get("query") or query_data.get("query")
    variables = data.get("variables") or query_data.get("variables")
    # document_id = data.get('documentId')
    operation_name = data.get(
        "operationName") or query_data.get("operationName")

    return GraphQLParams(query, load_json_variables(variables), operation_name)


def get_response(
    schema,  # type: GraphQLSchema
    params,  # type: GraphQLParams
    catch,  # type: Type[BaseException]
    allow_only_query=False,  # type: bool
    **kwargs  # type: Dict
):
    # type: (...) -> Optional[ExecutionResult]
    try:
        # execution_result = execute_graphql_request(
        #     schema, params, allow_only_query, **kwargs
        # )
        a = graphql(schema, query)
    except catch:
        return None

    return execution_result


def json_encode(data, pretty=False):
    # type: (Dict, bool) -> str
    if not pretty:
        return json.dumps(data, separators=(",", ":"))

    return json.dumps(data, indent=2, separators=(",", ": "))


def load_json_variables(variables):
    # type: (Optional[Union[str, Dict]]) -> Optional[Dict]
    if variables and isinstance(variables, six.string_types):
        try:
            return json.loads(variables)
        except Exception:
            raise HttpQueryError(400, "Variables are invalid JSON.")
    return variables  # type: ignore


def load_json_body(data):
    # type: (str) -> Dict
    try:
        return json.loads(data)
    except Exception:
        raise HttpQueryError(400, "POST body sent invalid JSON.")
