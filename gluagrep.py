import os.path
import re
import subprocess

from ..base import Plugin

class GLuaGrep(Plugin):
	def __init__(self):
		super(GLuaGrep, self).__init__()
		
		self.lastGrepLines = []
		self.lastGrepUrls  = []
		
		self.gitRepositories = {}
		self.gitRepositories["garrysmod"]          = "https://github.com/garrynewman/garrysmod.git"
		self.gitRepositories["darkrp"]             = "https://github.com/FPtje/DarkRP.git"
		self.gitRepositories["ulib"]               = "https://github.com/TeamUlysses/ulib.git"
		self.gitRepositories["ulx"]                = "https://github.com/TeamUlysses/ulx.git"
		self.gitRepositories["evolve"]             = "https://github.com/Xandaros/evolve.git"
		self.gitRepositories["wiremod"]            = "https://github.com/wiremod/wire.git"
		self.gitRepositories["advdupe"]            = "https://github.com/wiremod/advduplicator.git"
		self.gitRepositories["advdupe2"]           = "https://github.com/wiremod/advdupe2.git"
		self.gitRepositories["starfall"]           = "https://github.com/thegrb93/StarfallEx.git"
		self.gitRepositories["pac3"]               = "https://github.com/Metastruct/pac3.git"
		self.gitRepositories["glib"]               = "https://github.com/notcake/glib.git"
		self.gitRepositories["gooey"]              = "https://github.com/notcake/gooey.git"
		self.gitRepositories["vfs"]                = "https://github.com/notcake/vfs.git"
		self.gitRepositories["gcompute"]           = "https://github.com/notcake/gcompute.git"
		self.gitRepositories["gcad"]               = "https://github.com/notcake/gcad.git"
		self.gitRepositories["cac-administration"] = "https://github.com/notcake/cac-administration.git"
		
		self.gitRepositories["se2007"]             = "https://github.com/LestaD/SourceEngine2007.git"
		
		self.searchGroups = {}
		self.searchGroups["default"]            = [("git", "garrysmod", "garrysmod/gamemodes/base",       "gamemodes/base"),
		                                           ("git", "garrysmod", "garrysmod/gamemodes/sandbox",    "gamemodes/sandbox"),
		                                           ("git", "garrysmod", "garrysmod/lua",                  "lua")]
		self.searchGroups["game"]               = self.searchGroups["default"]
		self.searchGroups["garrysmod"]          = self.searchGroups["default"]
		self.searchGroups["gmod"]               = self.searchGroups["default"]
		
		# Gamemodes
		self.searchGroups["sandbox"]            = [("git", "garrysmod",         "garrysmod/gamemodes/sandbox",    "gamemodes/sandbox")]
		self.searchGroups["ttt"]                = [("git", "garrysmod",         "garrysmod/gamemodes/terrortown", "gamemodes/terrortown")]
		self.searchGroups["terrortown"]         = [("git", "garrysmod",         "garrysmod/gamemodes/terrortown", "gamemodes/terrortown")]
		self.searchGroups["darkrp"]             = [("git", "darkrp",            "",                               "gamemodes/darkrp")]
		
		# Admin mods
		self.searchGroups["ulx"]                = [("git", "ulib",              "lua",                            "addons/ulib/lua"),
		                                           ("git", "ulx",               "lua",                            "addons/ulx/lua")]
		self.searchGroups["ulib"]               = [("git", "ulib",              "lua",                            "addons/ulib/lua")]
		
		self.searchGroups["evolve"]             = [("git", "evolve",            "lua",                            "addons/evolve/lua")]
		
		# Sandbox
		self.searchGroups["wiremod"]            = [("git", "wiremod",           "lua",                            "addons/wiremod/lua")]
		self.searchGroups["wire"]               = self.searchGroups["wiremod"]
		
		self.searchGroups["advdupe"]            = [("git", "advdupe",           "lua",                            "addons/advduplicator/lua")]
		self.searchGroups["advdupe2"]           = [("git", "advdupe2",          "lua",                            "addons/advdupe2/lua")]
		
		self.searchGroups["starfall"]           = [("git", "starfall",          "lua",                            "addons/starfall/lua")]
		
		self.searchGroups["pac3"]               = [("git", "pac3",              "lua",                            "addons/pac3/lua")]
		self.searchGroups["pac"]                = self.searchGroups["pac3"]
		
		# !cake addons
		self.searchGroups["glib"]               = [("git", "glib",              "lua",                            "addons/glib/lua")]
		self.searchGroups["gooey"]              = [("git", "gooey",             "lua",                            "addons/gooey/lua")]
		self.searchGroups["vfs"]                = [("git", "vfs",               "lua",                            "addons/vfs/lua")]
		self.searchGroups["gcompute"]           = [("git", "gcompute",          "lua",                            "addons/gcompute/lua")]
		self.searchGroups["gcad"]               = [("git", "gcad",              "lua",                            "addons/gcad/lua")]
		
		self.searchGroups["cac"]                = [("git", "cac-administration", "",                              "addons/cac/lua/cac/administration")]
		self.searchGroups["cac-administration"] = self.searchGroups["cac"]
		
		# All
		all = []
		for addonName in sorted(self.searchGroups.keys()):
			searchGroup = self.searchGroups[addonName]
			for descriptor in searchGroup:
				if descriptor not in all:
					all.append(descriptor)
		
		self.searchGroups["all"] = all
		self.searchGroups["*"] = all
		
		# Engine
		self.searchGroups["source"]             = [("git", "se2007",           "",                                "")]
		self.searchGroups["engine"]             = [("git", "se2007",           "",                                "")]
		self.searchGroups["se2007"]             = [("git", "se2007",           "se2007",                          "se2007")]
		self.searchGroups["src_main"]           = [("git", "se2007",           "src_main",                        "src_main")]
	
	# Plugin
	def handleInitialize(self):
		self.registerCommand("git",   self.handleGit).setDescription("git")
		
		self.registerCommand("fgrep", self.handleSearch).setDescription("Searches the Garry's Mod codebase.").addParameter("addon name").addParameter("search text").setHelpText("where addon name is one of { " + ", ".join(sorted(self.searchGroups.keys())) + "}")
		self.registerCommand("grep",  self.handleSearch).setDescription("Searches the Garry's Mod codebase.").addParameter("addon name").addParameter("search text").setHelpText("where addon name is one of { " + ", ".join(sorted(self.searchGroups.keys())) + "}")
		
		self.registerCommand("link",  self.handleLink).setDescription("Prints a link from the previous search.").addParameter("number")
	
	def handleInitializeTemporaryChannelData(self, channel, channelData):
		channelData["lastGrepLines"] = []
		channelData["lastGrepUrls"]  = []
	
	def handleInitializeTemporaryUserData(self, user, userData):
		userData["lastGrepLines"] = []
		userData["lastGrepUrls"]  = []
	
	# GLuaGrep
	# Internal
	def handleGit(self, command, commandInvocation, message):
		if commandInvocation.arguments[0].text != "pull":
			message.channel.postMessage("!git pull")
			return
		
		self.updateRepositories(message.channel)
	
	def handleSearch(self, command, commandInvocation, message):
		if commandInvocation.argumentCount < 2:
			self.printSearchHelp(message, commandInvocation)
			return
		
		self.search(command, commandInvocation, message, commandInvocation.arguments[0].text, commandInvocation.remainingArguments(1))
	
	def handleLink(self, command, commandInvocation, message):
		n = None
		try:
			n = int(commandInvocation.arguments[0].text)
		except: pass
		
		if n is None:
			command.printUsage(message.channel)
			return
		
		if message.channel.isPrivateMessageChannel:
			lastGrepLines = self.getTemporaryUserData(message.author)["lastGrepLines"]
			lastGrepUrls  = self.getTemporaryUserData(message.author)["lastGrepUrls"]
		else:
			lastGrepLines = self.getTemporaryChannelData(message.channel)["lastGrepLines"]
			lastGrepUrls  = self.getTemporaryChannelData(message.channel)["lastGrepUrls"]
		
		if n >= len(lastGrepUrls):
			message.channel.postMessage("No previous grep result with that number found.")
			return
		
		message.channel.postMessage(lastGrepUrls[n] + "\n```\n" + lastGrepLines[n] + "```")
	
	def search(self, command, commandInvocation, message, addonName, searchText):
		if addonName.lower() not in self.searchGroups:
			command.printUsage(message.channel)
			return
		
		lines = []
		urls  = []
		
		aborted = False
		
		for descriptor in self.searchGroups[addonName.lower()]:
			type = descriptor[0]
			if type == "git":
				repositoryId = descriptor[1]
				directoryName = repositoryId
				subdirectory = descriptor[2]
				mountDirectory = descriptor[3]
				if mountDirectory is None: mountDirectory = subdirectory
				if len(mountDirectory) > 0: mountDirectory += "/"
				
				directory = os.path.join(self.dataDirectory, directoryName)
				directory = os.path.join(directory, subdirectory)
				
				aborted, matches = self.fgrep(searchText, directory)
				
				repositoryUrl = self.gitRepositories[repositoryId]
				repositoryUrl = repositoryUrl[:-4] + "/tree/master/"
				if len(subdirectory) > 0:
					repositoryUrl += subdirectory + "/"
				
				for match in matches:
					lines.append(("[%2d]" % len(lines)) + " " + mountDirectory + match)
					
					match = re.match("^([^:]+):([0-9]+):", match)
					url = repositoryUrl + match.group(1) + "#L" + match.group(2)
					urls.append(url)
				
				if aborted: break
		
		aborted = len(lines) > 10
		lines = lines[0:10]
		urls  = urls[0:10]
		
		if len(lines) == 0:
			message.channel.postMessage("No results found!")
			return
		
		if not message.channel.isPrivateMessageChannel:
			self.getTemporaryChannelData(message.channel)["lastGrepLines"] = lines
			self.getTemporaryChannelData(message.channel)["lastGrepUrls"]  = urls
		
		self.getTemporaryUserData(message.author)["lastGrepLines"]     = lines
		self.getTemporaryUserData(message.author)["lastGrepUrls"]      = urls
		
		output = "!link <number> to get a hyperlink.\n"
		output += "\n".join(lines)
		if aborted: output += "\n..."
		output = "```lua\n" + output + "```"
		
		message.channel.postMessage(output)
	
	def fgrep(self, searchText, directory):
		output = None
		try:
			output = subprocess.check_output(["fgrep", "-i", "-n", "--binary-files=without-match", "-r", searchText, "."], cwd = directory)
		except:
			output = b""
		
		output = output.decode("utf-8")
		output = output.strip()
		
		if output == "": return False, []
		
		rawLines = output.split("\n")
		
		prettifiedLines = []
		aborted = False
		
		for line in rawLines:
			if len(prettifiedLines) > 10:
				aborted = True
				break
			
			if line[0:2] == "./":
				line = line[2:]
			
			prettifiedLines.append(line)
		
		return aborted, prettifiedLines
	
	def updateRepositories(self, channel = None):
		reply = []
		
		for directoryName, url in self.gitRepositories.items():
			output = self.clonePullGitRepository(url, directoryName)
			reply.append(output)
			
			self.log(output)
		
		if channel is None: return
		
		reply = "\n".join(reply)
		reply = "```\n" + reply + "```"
		channel.postMessage(reply)
	
	def clonePullGitRepository(self, url, directoryName):
		output = None
		directory = os.path.join(self.dataDirectory, directoryName)
		if not os.path.exists(directory):
			output = subprocess.check_output(["git", "clone", url, directory], env = { "GIT_TERMINAL_PROMPT": "0" })
			output = "Cloned " + url + " into " + directoryName + "."
		else:
			output = subprocess.check_output(["git", "pull"], cwd = directory)
			output = output.decode("utf-8")
			output = output.strip()
			output = directoryName + ": " + output
		
		return output
