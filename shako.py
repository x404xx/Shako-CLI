from asyncio import run
from base64 import urlsafe_b64encode
from json import dumps, loads
from textwrap import dedent
from uuid import uuid4

import websockets
from rich.console import Console
from rich.markdown import Markdown


class Colors:
    GREEN = '\033[38;5;121m'
    END = '\033[0m'


class ShakoChatbot:
    OPTIONS = """
        Shako - A command-line tool for interacting with Shako AI chatbot. (https://shako.ai)
            DOUBLE "enter" to send a message.
            - Type "!exit" to exit the program.
            - Type "!clear" to clear the console.
            - Type "!new" to start a new conversation.
    """

    def __init__(self):
        self.console = Console()
        self.websocket = None
        self.chat_id = None
        self.conversation = []
        self.uri = 'wss://api.shako.ai/api/chat'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
            'Sec-WebSocket-Version': '13',
            'Origin': 'https://shako.ai',
            'Sec-WebSocket-Extensions': 'permessage-deflate',
            'Sec-WebSocket-Key': self.web_key(),
            'Connection': 'Upgrade',
        }

    def web_key(self):
        return urlsafe_b64encode(uuid4().bytes).decode('utf-8')

    def get_query(
        self, prompt
        ):

        print(prompt, end='')
        return '/n'.join(iter(input, ''))

    async def process_response(
        self, response
        ):

        result = ''
        while True:
            response_data = loads(response)
            content = response_data.get('content')
            if content:
                result += content
            response_type = response_data.get('type')
            if response_type == 'end':
                break
            response = await self.websocket.recv()

        return result.strip(), response_data.get('chat_id')

    async def send_initial_data(
        self, initial_data
        ):

        await self.websocket.send(dumps(initial_data))
        response = await self.websocket.recv()
        result, chat_id = await self.process_response(response)
        return result, chat_id

    async def initial_data(
        self, query
        ):

        return {
            'chat_id': str(uuid4()) if self.chat_id is None else self.chat_id,
            'metadata': {},
            'prompt': self.conversation + [{'content': query, 'role': 'user'}]
        }

    async def connect(self):
        while True:
            query = self.get_query(f'{Colors.GREEN}You{Colors.END} : ').lower()
            if query == '!exit':
                break
            elif query == '!clear':
                self.console.clear()
                print(dedent(self.OPTIONS))
            elif query == '!new':
                self.console.clear()
                print(dedent(self.OPTIONS))
                self.chat_id = None
                self.conversation = []
            else:
                initial_data = await self.initial_data(query)
                with self.console.status("[bold blue]Please wait! Shako is thinking..[/bold blue]", spinner='point'):
                    async with websockets.connect(self.uri, extra_headers=self.headers) as self.websocket:
                        result, chat_id = await self.send_initial_data(initial_data)
                        self.console.print(Markdown(result, code_theme='fruity'))
                        self.chat_id = chat_id
                        print()

                        self.conversation.extend([
                            {'content': query, 'role': 'user'},
                            {'content': result, 'role': 'model'},
                        ])

    def run(self):
        self.console.clear()
        print(dedent(self.OPTIONS))
        run(self.connect())


if __name__ == '__main__':
    ShakoChatbot().run()
