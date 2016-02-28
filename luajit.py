import re
import unicodedata

from ..base import Plugin

class LuaJitRepl(Plugin):
	# Plugin
	def handleInitialize(self):
		pass
	
	def handleUninitialize(self):
		pass
	
	def handleEnabled(self):
		self.chatbot.messageReceived.addListener("LuaJitRepl", self.handleMessageReceived)
	
	def handleDisabled(self):
		self.chatbot.messageReceived.removeListener("LuaJitRepl")
	
	# Unicode
	# Internal
	def handleMessageReceived(self, chatbot, message):
		text = message.content
		if not text.startswith("u\""): return
		
		text = text[2:]
		if text.endswith("\""):
			text = text[:-1]
		
		bytes = b""
		lines = []
		for i in range(0, min(10, len(text))):
			c = text[i]
			
			bytes += c.encode("utf-8")
			lines.append(self.formatCharacterInformation(c))
		
		escapedString = "\""
		for uint8 in bytes:
			if 0x20 <= uint8 and uint8 < 0x7F:
				escapedString += chr(uint8)
			else:
				escapedString += "\\x%02x" % uint8
		escapedString += "\""
		
		reply = escapedString + "\n" + "\n".join(lines)
		reply = "```\n" + reply + "```"
		message.channel.postMessage(reply)
	
	def handleUnicodeSearch(self, message, commandInvocation):
		searchText = commandInvocation.fullArguments.strip()
		searchText = searchText.lower()
		
		if len(searchText) == 0:
			message.channel.postMessage("You must provide a search term!")
			return
		
		results = []
		aborted = False
		for i in range(0, 0x110000):
			c = chr(i)
			name = unicodedata.name(c, "").lower()
			if searchText in name:
				if len(results) >= 5:
					aborted = True
					break
				else:
					results.append(self.formatCharacterInformation(c))
		
		if len(results) == 0:
			message.channel.postMessage("No matching code points found :(")
		else:
			if aborted: results.append("...")
			reply = "\n".join(results)
			reply = "```\n" + reply + "```"
			
			message.channel.postMessage(reply)
	
	def formatCharacterInformation(self, c):
		codePoint = ord(c)
		printableCharacter = c
		if unicodedata.category(c) in ("Zs", "Zl", "Zp", "Cc", "Cf", "Cs", "Co", "Cn"):
			printableCharacter = " "
		name = unicodedata.name(c, "")
		
		return "U+%06X %s %s" % (codePoint, printableCharacter, name)
