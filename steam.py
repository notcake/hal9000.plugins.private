import re

from ..base import Plugin

from .steamapi import SteamId
from .steamapi import SteamProfile

class Steam(Plugin):
	# Plugin
	def handleInitialize(self):
		self.registerCommand("steam", self.handleSteam).setDescription("Resolve a Steam profile.")
	
	# Ping
	# Internal
	def handleSteam(self, command, commandInvocation, message):
		text = commandInvocation.fullArguments
		
		steamId      = None
		steamProfile = None
		if steamId is None: steamId = SteamId.fromSteamId(text)
		if steamId is None: steamId = SteamId.fromSteamId3(text)
		if steamId is None: steamId = SteamId.fromSteamId64(text)
		if steamId is None: steamId = SteamId.fromProfileUrl(text)
		
		if steamId is None:
			steamProfile = SteamProfile.fromCustomProfileUrl(text)
			if steamProfile is None:
				message.channel.postMessage("Unable to parse Steam ID.")
				return
			
			steamId = steamProfile.steamId
		else:
			steamProfile = SteamProfile.fromSteamId(steamId)
		
		content = ""
		if steamProfile is not None and \
		   steamProfile.displayName is not None:
			content += "Display Name: " + steamProfile.displayName + "\n"
		content += "SteamID: "   + steamId.steamId        + "\n"
		content += "SteamID3: "  + steamId.steamId3       + "\n"
		content += "SteamID64: " + str(steamId.steamId64) + "\n"
		content += "Profile: "   + steamId.profileUrl     + "\n"
		if steamProfile is not None and \
		   steamProfile.customProfileUrl is not None:
			content += "Profile: " + steamProfile.customProfileUrl + "\n"
		
		message.channel.postMessage(content)
