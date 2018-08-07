import asyncio

from graphql import (
    graphql,
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString
)
from typing import Sequence
from sanic import Sanic
# from sanic.response import json
from nextql import GraphQLView


class Character:
    id: str
    name: str
    friends: Sequence[str]
    appearsIn: Sequence[str]

# noinspection PyPep8Naming


class Droid(Character):
    type = 'Droid'
    primaryFunction: str

    # noinspection PyShadowingBuiltins
    def __init__(self, id, name, friends, appearsIn, primaryFunction):
        self.id, self.name = id, name
        self.friends, self.appearsIn = friends, appearsIn
        self.primaryFunction = primaryFunction


class Human(Character):
    type = 'Human'
    homePlanet: str

    # noinspection PyShadowingBuiltins
    def __init__(self, id, name, friends, appearsIn, homePlanet):
        self.id, self.name = id, name
        self.friends, self.appearsIn = friends, appearsIn
        self.homePlanet = homePlanet


def get_character(id):
    return None


def get_friends(character):
    return None


def get_hero(id):
    return Human(
        id='1000',
        name='Luke Skywalker',
        friends=['1002', '1003', '2000', '2001'],
        appearsIn=[4, 5, 6],
        homePlanet='Tatooine'
    )


def get_human(id):
    return None


def get_droid(id):
    return Droid(
        id='2001',
        name='R2-D2',
        friends=['1000', '1002', '1003'],
        appearsIn=[4, 5, 6],
        primaryFunction='Astromech'
    )


def get_secret_backstory(character):
    return None


episode_enum = GraphQLEnumType('Episode', {
    'NEWHOPE': GraphQLEnumValue(4, description='Released in 1977.'),
    'EMPIRE': GraphQLEnumValue(5, description='Released in 1980.'),
    'JEDI': GraphQLEnumValue(6, description='Released in 1983.')
}, description='One of the films in the Star Wars Trilogy')


character_interface = GraphQLInterfaceType('Character', lambda: {
    'id': GraphQLField(
        GraphQLNonNull(GraphQLString),
        description='The id of the character.'),
    'name': GraphQLField(
        GraphQLString,
        description='The name of the character.'),
    'friends': GraphQLField(
        GraphQLList(character_interface),
        description='The friends of the character,'
                    ' or an empty list if they have none.'),
    'appearsIn': GraphQLField(
        GraphQLList(episode_enum),
        description='Which movies they appear in.'),
    'secretBackstory': GraphQLField(
        GraphQLString,
        description='All secrets about their past.')},
    resolve_type=lambda character, _info:
        {'Human': human_type, 'Droid': droid_type}.get(character.type),
    description='A character in the Star Wars Trilogy')


human_type = GraphQLObjectType(
    'Human',
    lambda: {
        'id': GraphQLField(
            GraphQLNonNull(GraphQLString),
            description='The id of the human.'),
        'name': GraphQLField(
            GraphQLString,
            description='The name of the human.'),
        'friends': GraphQLField(
            GraphQLList(character_interface),
            description='The friends of the human,'
                        ' or an empty list if they have none.',
            resolve=lambda human, _info: get_friends(human)),
        'appearsIn': GraphQLField(
            GraphQLList(episode_enum),
            description='Which movies they appear in.'),
        'homePlanet': GraphQLField(
            GraphQLString,
            description='The home planet of the human, or null if unknown.'),
        'secretBackstory': GraphQLField(
            GraphQLString,
            resolve=lambda human, _info: get_secret_backstory(human),
            description='Where are they from'
                        ' and how they came to be who they are.')
    },
    interfaces=[character_interface],
    description='A humanoid creature in the Star Wars universe.')


droid_type = GraphQLObjectType('Droid', lambda: {
    'id': GraphQLField(
        GraphQLNonNull(GraphQLString),
        description='The id of the droid.'),
    'name': GraphQLField(
        GraphQLString,
        description='The name of the droid.'),
    'friends': GraphQLField(
        GraphQLList(character_interface),
        description='The friends of the droid,'
                    ' or an empty list if they have none.',
        resolve=lambda droid, _info: get_friends(droid),
    ),
    'appearsIn': GraphQLField(
        GraphQLList(episode_enum),
        description='Which movies they appear in.'),
    'secretBackstory': GraphQLField(
        GraphQLString,
        resolve=lambda droid, _info: get_secret_backstory(droid),
        description='Construction date and the name of the designer.'),
    'primaryFunction': GraphQLField(
        GraphQLString,
        description='The primary function of the droid.')
},
    interfaces=[character_interface],
    description='A mechanical creature in the Star Wars universe.')


query_type = GraphQLObjectType(
    'Query', lambda: {
        'hero': GraphQLField(
            character_interface,
            args={
                'episode': GraphQLArgument(
                    episode_enum,
                    description=(
                        'If omitted, returns the hero of the whole saga.'
                        ' If provided, returns the hero of that particular episode.'
                    )
                )
            },
            resolve=lambda root, _info, episode=None: get_hero(episode)
        ),
        'human': GraphQLField(
            human_type,
            args={
                'id': GraphQLArgument(
                    GraphQLNonNull(GraphQLString),
                    description='id of the human')
            },
            resolve=lambda root, _info, id: get_human(id)
        ),
        'droid': GraphQLField(
            droid_type,
            args={
                'id': GraphQLArgument(
                    GraphQLNonNull(GraphQLString),
                    description='id of the droid'
                )
            },
            resolve=lambda root, _info, id: get_droid(id)
        )
    }
)

star_wars_schema = GraphQLSchema(query_type, types=[human_type, droid_type])


query = """
    query HeroNameQuery {
        hero {
            name
        }
    }
"""


# async def main():
#     print('Fetching the result...')

#     print(result)


# loop = asyncio.get_event_loop()
# try:
#     loop.run_until_complete(main())
# finally:
#     loop.close()


app = Sanic()


# @app.route('/')
# async def test(request):
#     result = await graphql(star_wars_schema, query)
#     return json(result)

app.add_route(GraphQLView.as_view(
    schema=star_wars_schema), '/graphql')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
