from .cowsaynsfw import CowSayNsfw
from .glua       import GLua
from .gluagrep   import GLuaGrep
from .steam      import Steam

def register(chatbot):
	chatbot.addPlugin(GLuaGrep)
	chatbot.addPlugin(GLua)
	chatbot.addPlugin(CowSayNsfw)
	chatbot.addPlugin(Steam)
