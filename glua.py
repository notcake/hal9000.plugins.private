import re
import subprocess

from ..base import Plugin

class GLua(Plugin):
	def __init__(self):
		super(GLua, self).__init__()
		
		self.indexInitialized       = False
		self.pageNames              = set()
		self.lowercasePageNames     = {}
		self.categoryNames          = set()
		self.lowercaseCategoryNames = {}
		
		self.urlCache               = {}
	
	# Plugin
	def handleInitialize(self):
		self.registerCommand("glua", self.handleGLua).setDescription("Summons the Garry's Mod Lua documentation.").addParameter("function name")
	
	# GLua
	# Internal
	def handleGLua(self, command, commandInvocation, message):
		if not self.indexInitialized:
			self.initializeIndex()
		
		name = commandInvocation.fullArguments
		name = re.sub(":", ".", name)
		
		pageName = self.toPageName(name)
		
		handled = False
		
		# Metatable
		if name.upper().startswith("_R."):
			if "." in name[3:]:
				handled = self.tryHandlePage(message, pageName[3:], name[3:]) or handled
			else:
				handled = self.tryHandleCategory(message, pageName[3:], name[3:]) or handled
		elif name.upper().startswith("_G."):
			name = name[3:]
		
		# Library function
		handled = self.tryHandlePage(message, pageName, name) or handled
		
		# Global
		handled = self.tryHandlePage(message, "Global/" + pageName, name) or handled
		
		# Hook
		handled = self.tryHandlePage(message, "GM/" + pageName, "GM:" + name) or handled
		
		# Class hooks
		if "." not in name:
			categoryName = pageName.upper() + " Hooks"
			className = name.upper()
			handled = self.tryHandleCategory(message, categoryName, className) or handled
		
		# Category
		if "." not in name:
			handled = self.tryHandleCategory(message, pageName, name) or handled
		
		# Search
		if not handled:
			aborted       = False
			pageNames     = []
			categoryNames = []
			if not aborted: aborted, pageNames     = self.findPages(pageName)
			if not aborted: aborted, categoryNames = self.findCategories(pageName)
			
			if len(pageNames) + len(categoryNames) == 0:
				pass
			elif len(pageNames) == 1 and len(categoryNames) == 0:
				pageName = pageNames[0]
				handled = self.tryHandlePage(message, pageName, self.toName(pageName)) or handled
			elif len(pageNames) == 0 and len(categoryNames) == 1:
				categoryName = categoryNames[0]
				handled = self.tryHandleCategory(message, categoryName, self.toName(categoryName)) or handled
			else:
				handled = True
				categoryNames = ["Category:" + categoryName for categoryName in categoryNames]
				pageNames = pageNames + categoryNames
				aborted = aborted or len(pageNames) > 10
				pageNames = pageNames[0:10]
				pageNames = ["http://wiki.garrysmod.com/page/" + self.toUrl(pageName) for pageName in pageNames]
				
				message.channel.postMessage("\n".join(pageNames))
			
			if not handled:
				message.channel.postMessage("Cannot find an exact match for \"" + commandInvocation.fullArguments + "\".")
	
	def tryHandlePage(self, message, pageName, name):
		pageName = self.resolvePageName(pageName)
		if pageName is None: return None
		
		return self.handlePage(message, pageName, name)
	
	def tryHandleCategory(self, message, categoryName, name):
		categoryName = self.resolveCategoryName(categoryName)
		if categoryName is None: return None
		
		return self.handleCategory(message, categoryName, name)
	
	def handleCategory(self, message, categoryName, name):
		# Fetch
		url = "http://wiki.garrysmod.com/api.php?format=xml&action=query&list=categorymembers&cmlimit=max&cmtitle=Category:" + self.toUrl(categoryName)
		data = self.getPage(url)
		if data is None: return False
		
		# Extract method names
		methodNames = []
		for match in re.finditer("title=\"([^\"]+)\"", data):
			methodName = match.group(1)
			methodName = re.sub("/", ".", methodName)
			methodNames.append(methodName)
		
		maximumLength = max(map(len, methodNames)) if len(methodNames) > 0 else 0
		methodNames = [x.ljust(maximumLength) for x in methodNames]
		
		# Truncate
		truncated = False
		if len(methodNames) > 40:
			methodNames = methodNames[0:40]
			truncated = True
		
		# Split into columns
		linesPerColumn = int(len(methodNames) / 4.0 + 0.5)
		methodNames1 = methodNames[0:linesPerColumn]
		methodNames2 = methodNames[linesPerColumn:2 * linesPerColumn]
		methodNames3 = methodNames[2 * linesPerColumn:3 * linesPerColumn]
		methodNames4 = methodNames[3 * linesPerColumn:]
		
		# Merge
		lines = []
		for i in range(0, linesPerColumn):
			s1 = methodNames1[i]
			s2 = methodNames2[i] if i < len(methodNames2) else "".ljust(maximumLength)
			s3 = methodNames3[i] if i < len(methodNames3) else "".ljust(maximumLength)
			s4 = methodNames4[i] if i < len(methodNames4) else "".ljust(maximumLength)
			lines.append(s1 + "    " + s2 + "    " + s3 + "    " + s4)
		
		if truncated: lines.append("...")
		
		reply = "http://wiki.garrysmod.com/page/Category:" + self.toUrl(categoryName)
		reply += "\n```lua\n" + "\n".join(lines) + "```"
		
		message.channel.postMessage(reply)
		
		return True
	
	def handlePage(self, message, pageName, name):
		# Fetch
		url = "http://wiki.garrysmod.com/page/" + self.toUrl(pageName) + "?action=raw"
		data = self.getPage(url)
		if data is None: return False
		
		if data.startswith("#REDIRECT [["): return False
		
		url = "http://wiki.garrysmod.com/page/" + self.toUrl(pageName)
		
		if "{{Func" in data or "{{Hook" in data or "{{Arg" in data:
			self.handleFunction(message, url, name, data)
		else:
			message.channel.postMessage(url)
		
		return True
	
	def handleFunction(self, message, url, name, data):
		reply = url
		
		functionDescription = self.getBlob(data, "Func")
		isHook = False
		if functionDescription is None:
			functionDescription = self.getBlob(data, "Hook")
			isHook = functionDescription is not None
		qualifiedName = name
		
		# Function description
		if functionDescription is not None:
			functionParent = self.getBlobAttribute(functionDescription, "Parent")
			functionName = self.getBlobAttribute(functionDescription, "Name")
			functionIsMember = self.getBlobAttribute(functionDescription, "IsClass") == "Yes"
			functionDescription = self.getBlobAttribute(functionDescription, "Description")
			if functionParent == "Global": functionParent = None
			
			if functionParent is None:
				qualifiedName = functionName
				if qualifiedName is None: qualifiedName = name
			elif functionIsMember or isHook:
				qualifiedName = functionParent + ":" + functionName
			else:
				qualifiedName = functionParent + "." + functionName
		
		# Return values
		returnValues = []
		returnDescriptions = []
		for returnDescription in self.getBlobs(data, "Ret"):
			returnValues.append(self.getBlobAttribute(returnDescription, "type", "???"))
			returnDescriptions.append(self.getBlobAttribute(returnDescription, "desc", "???"))
		
		# Parameters
		parameters = []
		parameterNames = []
		parameterTypes = []
		parameterDescriptions = []
		for parameterDescription in self.getBlobs(data, "Arg"):
			parameterType = self.getBlobAttribute(parameterDescription, "type", None)
			parameterName = self.getBlobAttribute(parameterDescription, "name", "_")
			if parameterType == "vararg":
				parameterType = None
				parameterName = "..."
			
			parameterTypes.append(parameterType)
			parameterNames.append(parameterName)
			if parameterType is not None:
				parameters.append(parameterType + " " + parameterName)
			else:
				parameters.append(parameterName)
			
			parameterDescriptions.append(self.getBlobAttribute(parameterDescription, "desc", ""))
		
		# Format output
		reply += "\n```lua\n"
		if len(returnValues) > 0:
			reply += ", ".join(returnValues)
			reply += " = "
		reply += "function "
		reply += qualifiedName
		reply += "("
		reply += ", ".join(parameters)
		reply += ")"
		reply += "```"
		
		# Description
		if functionDescription is not None and \
		   "{" not in functionDescription and \
		   "}" not in functionDescription:
			reply += "\n" + functionDescription
		
		message.channel.postMessage(reply)
	
	def getBlob(self, data, type):
		regex = re.compile(r".*?(\{\{" + type + r"[^\}]*\}\})", re.DOTALL)
		match = regex.match(data)
		if match is None: return None
		
		return match.group(1)
	
	def getBlobs(self, data, type):
		return re.findall(r"\{\{" + type + r"[^\}]*\}\}", data)
	
	def getBlobAttribute(self, blob, attributeName, default = None):
		regex = re.compile(r".*?\|" + attributeName + r"=([^\|\}]*)", re.DOTALL)
		match = regex.match(blob)
		if match is None: return default
		
		return match.group(1).strip()
	
	# Index
	def initializeIndex(self):
		if self.indexInitialized: return
		
		pageList = self.getPage("http://wiki.garrysmod.com/api.php?format=xml&action=query&list=allpages&aplimit=max")
		for match in re.finditer("title=\"([^\"]+)\"", pageList):
			pageName = match.group(1)
			self.pageNames.add(pageName)
			self.lowercasePageNames[pageName.lower()] = pageName
		
		pageList = self.getPage("http://wiki.garrysmod.com/api.php?format=xml&action=query&list=allcategories&aclimit=max")
		for match in re.finditer("<c xml:space=\"preserve\">([^<]+)</c>", pageList):
			categoryName = match.group(1)
			self.categoryNames.add(categoryName)
			self.lowercaseCategoryNames[categoryName.lower()] = categoryName
		
		self.log("Initialized index (" + str(len(self.pageNames)) + " pages and " + str(len(self.categoryNames)) + " categories).")
		
		self.indexInitialized = True
	
	def toName(self, pageName):
		name = pageName
		name = re.sub(r"/", ".", name)
		return name
	
	def toPageName(self, name):
		pageName = name
		pageName = re.sub(r" ", "_", pageName)
		pageName = re.sub(r"[:\.]", "/", pageName)
		return pageName
	
	def toUrl(self, pageName):
		url = pageName
		url = re.sub(r" ", "_", url)
		return url
	
	def resolvePageName(self, pageName):
		if pageName is None: return None
		
		if pageName in self.pageNames: return pageName
		
		return self.lowercasePageNames.get(pageName.lower())
	
	def resolveCategoryName(self, categoryName):
		if categoryName is None: return None
		
		if categoryName in self.categoryNames: return categoryName
		
		return self.lowercaseCategoryNames.get(categoryName.lower())
	
	def findPages(self, pageNameFragment, limit = 10):
		aborted = False
		pageNames = []
		
		pageNameFragment = pageNameFragment.lower()
		for lowercasePageName in sorted(self.lowercasePageNames.keys()):
			if pageNameFragment in lowercasePageName:
				if len(pageNames) >= limit:
					aborted = True
					break
				
				pageNames.append(self.lowercasePageNames[lowercasePageName])
		
		return aborted, pageNames
	
	def findCategories(self, categoryNameFragment, limit = 10):
		aborted = False
		categoryNames = []
		
		categoryNameFragment = categoryNameFragment.lower()
		for lowercaseCategoryName in sorted(self.lowercaseCategoryNames.keys()):
			if categoryNameFragment in lowercaseCategoryName:
				if len(categoryNames) >= limit:
					aborted = True
					break
				
				categoryNames.append(self.lowercaseCategoryNames[lowercaseCategoryName])
		
		return aborted, categoryNames
	
	# URL Cache
	def getPage(self, url):
		if url in self.urlCache: return self.urlCache[url]
		
		output = subprocess.check_output(["curl", "-A", "Garry's Mod Developers Discord Bot", url])
		
		if len(output) == 0:
			output = None
		else:
			output = output.decode("utf-8")
		
		self.urlCache[url] = output
		
		return output
