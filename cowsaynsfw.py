from ..base import CowSay

class CowSayNsfw(CowSay):
	# Plugin
	def handleInitialize(self):
		super(CowSayNsfw, self).handleInitialize()
		
		self.registerCommand("dergsay",   self.handleDragonSay).setDescription("Rawr.")
		self.registerCommand("ponysay",   self.handlePonySay).setDescription("mcd1992 is a faggot.")
		self.registerCommand("sheepsay",  self.handleSheepSay).setDescription("Baaa.")
		
		for _, command in self.commands.items():
			command.addParameter("message")
	
	# CowSayNsfw
	# Internal
	def handleDragonSay(self, command, commandInvocation, message):
		self.handleSay(command, commandInvocation, message, commandInvocation.fullArguments, "dragon-and-cow")
	
	def handlePonySay(self, command, commandInvocation, message):
		self.handleSay(command, commandInvocation, message, commandInvocation.fullArguments, "unipony-smaller")
	
	def handleSheepSay(self, command, commandInvocation, message):
		self.handleSay(command, commandInvocation, message, commandInvocation.fullArguments, "sodomized-sheep")
