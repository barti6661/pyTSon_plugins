import ts3defines, ts3lib
from pluginhost import PluginHost
from ts3plugin import ts3plugin
from bluscream import timestamp
from pytson import getPluginPath

class quickMod(ts3plugin):
    path = getPluginPath("scripts", __name__)
    name = "Quick Moderation"
    apiVersion = 22
    requestAutoload = False
    version = "1.0"
    author = "Bluscream"
    description = "Allows you to set hotkeys for quick moderation (ban/restrict/remove tp)"
    offersConfigure = False
    commandKeyword = "qm"
    infoTitle = None
    menuItems = []
    hotkeys = [
        ("restrict_last_joined_server", "Restrict the last user that joined your server."),
        ("restrict_last_joined_channel", "Restrict the last user that joined your channel."),
        ("ban_last_joined_server", "Bans the last user that joined your server."),
        ("ban_last_joined_channel", "Bans the last user that joined your channel."),
        ("revoke_last_talk_power", "Restrict the last user that got talk power in your channel.")
    ]
    last_joined_server = 0
    last_joined_channel = 0
    last_talk_power = 0
    sgids = [17,21,83]
    requested = 0
    requestedIP = 0
    retcode = ""
    customBan = None
    bantime = 2678400
    banreason = "Ban Evading / Bannumgehung"

    def __init__(self):
        if PluginHost.cfg.getboolean("general", "verbose"): ts3lib.printMessageToCurrentTab("{0}[color=orange]{1}[/color] Plugin for pyTSon by [url=https://github.com/{2}]{2}[/url] loaded.".format(timestamp(),self.name,self.author))

    def processCommand(self, schid, keyword): self.onHotkeyOrCommandEvent(keyword, schid)

    def onHotkeyEvent(self, keyword): self.onHotkeyOrCommandEvent(keyword)

    def onHotkeyOrCommandEvent(self, keyword, schid=0):
        schid = ts3lib.getCurrentServerConnectionHandlerID()
        if keyword == "restrict_last_joined_server":
            self.requested = self.last_joined_server
            ts3lib.requestClientVariables(schid, self.last_joined_server)
            # self.restrictClient(schid, self.last_joined_server)
        elif keyword == "restrict_last_joined_channel":
            self.requested = self.last_joined_channel
            ts3lib.requestClientVariables(schid, self.last_joined_channel)
            # self.restrictClient(schid, self.last_joined_channel)
        elif keyword == "ban_last_joined_server":
            self.banClient(schid, self.last_joined_server)
        elif keyword == "ban_last_joined_channel":
            self.banClient(schid, self.last_joined_channel)
        elif keyword == "revoke_last_talk_power_channel":
            self.revokeTalkPower(schid, self.last_talk_power)

    def onUpdateClientEvent(self, schid, clid, invokerID, invokerName, invokerUniqueIdentifier):
        if clid == self.requestedIP:
            self.requestedIP = 0
            (err, ip) = ts3lib.getConnectionVariable(schid, clid, ts3defines.ConnectionProperties.CONNECTION_CLIENT_IP)
            self.banIP(schid, ip)
            return
        (err, ownID) = ts3lib.getClientID(schid)
        (err, cid) = ts3lib.getChannelOfClient(schid, clid)
        (err, ownCID) = ts3lib.getChannelOfClient(schid, ownID)
        (err, talker) = ts3lib.getClientVariable(schid, clid, ts3defines.ClientPropertiesRare.CLIENT_IS_TALKER)
        if cid == ownCID and talker: self.last_talk_power = clid
        if clid == self.requested:
            self.requested = 0
            if talker == 1: self.revokeTalkPower(schid, clid, True)
            # else: self.revokeTalkPower(schid, clid, False)
            (err, cldbid) = ts3lib.getClientVariable(schid, clid, ts3defines.ClientPropertiesRare.CLIENT_DATABASE_ID)
            (err, sgids) = ts3lib.getClientVariable(schid, clid, ts3defines.ClientPropertiesRare.CLIENT_SERVERGROUPS)
            if set(self.sgids).issubset(sgids):
                for sgid in self.sgids: ts3lib.requestServerGroupDelClient(schid, sgid, cldbid)
            else:
                for sgid in self.sgids: ts3lib.requestServerGroupAddClient(schid, sgid, cldbid)

    def revokeTalkPower(self, schid, clid, revoke=True):
        self.retcode = ts3lib.createReturnCode()
        ts3lib.requestClientSetIsTalker(schid, clid, revoke, self.retcode)

    def banClient(self, schid, clid):
        (err, uid) = ts3lib.getClientVariable(schid, clid, ts3defines.ClientProperties.CLIENT_UNIQUE_IDENTIFIER)
        (err, ip) = ts3lib.getConnectionVariable(schid, clid, ts3defines.ConnectionProperties.CONNECTION_CLIENT_IP)
        if not ip: self.requestedIP = clid; ts3lib.requestConnectionInfo(schid, clid)
        else: self.banIP(schid, ip)
        self.banUID(schid, uid)


    def banUID(self, schid, uid): ts3lib.banadd(schid, "", "", uid, self.bantime, self.banreason)

    def banIP(self, schid, ip):
        if not ip: return
        active = PluginHost.active
        if "Custom Ban" in active:
            whitelist = active["Custom Ban"].whitelist
            print("whitelist",whitelist)
            if len(whitelist) > 1:
                if ip in whitelist: ts3lib.printMessageToCurrentTab("{}: [color=red]Not banning whitelisted IP [b]{}".format(self.name, ip)); return
            else: ts3lib.printMessageToCurrentTab("{}: \"Custom Ban\"'s IP Whitelist faulty, please check!".format(self.name)); return
        ts3lib.banadd(schid, ip, "", "", self.bantime, self.banreason)

    def onClientMoveEvent(self, schid, clid, oldChannelID, newChannelID, visibility, moveMessage):
        if schid != ts3lib.getCurrentServerConnectionHandlerID(): return
        if oldChannelID == 0: self.last_joined_server = clid
        (err, ownID) = ts3lib.getClientID(schid)
        (err, ownCID) = ts3lib.getChannelOfClient(schid, ownID)
        if newChannelID == ownCID: self.last_joined_channel = clid

    def onServerErrorEvent(self, schid, errorMessage, error, returnCode, extraMessage):
        if returnCode == self.retcode: return True