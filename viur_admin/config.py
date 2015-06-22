#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from hashlib import sha512


class Config(object):
    def __init__(self):
        object.__init__(self)
        self.storagePath = os.path.join(os.path.expanduser("~"), ".viuradmin")
        if not os.path.isdir(self.storagePath):
            os.mkdir(self.storagePath)
        self.accounts = []
        self.portal = {}
        self.adminConfig = {}
        self.serverConfig = {"modules": {}}
        self.currentPortalConfigDirectory = None
        self.currentUsername = None  # Store the current Username/Password sothat
        self.currentPassword = None  # plugins are able to authenticate against other services
        self.availableLanguages = {}
        self.cmdLineOpts = None
        self.loadConfig()

    def xor(self, data, key=None):
        """This applys at least some *VERY BASIC* obscurfaction to saved passwords
        DO NOT RELY ON THIS TO GUARD ANYTHING"""
        key = bytes([x for x in range(0, 254)])
        klen = len(key)
        res = []
        for i in range(0, len(data)):
            res.append(data[i] ^ key[i % klen])
        return bytes(res)

    def loadConfig(self):
        # Load stored accounts
        configFileName = os.path.join(self.storagePath, "accounts.dat")
        try:
            configFileObject = open(configFileName, "rb")
            configData = self.xor(configFileObject.read()).decode("UTF-8")
            cfg = json.loads(configData)
            self.accounts = cfg
        except:
            try:  #Loading it from the old directory
                configFileObject = open(os.path.join(os.path.join(os.path.expanduser("~"), ".fwadmin"), "accounts.dat"),
                                        "rb")
                configData = self.xor(configFileObject.read()).decode("UTF-8")
                cfg = json.loads(configData)
                self.accounts = cfg
            except:
                print("Could not load Accounts")
                self.accounts = []
        #Load rest of the config
        configFileName = os.path.join(self.storagePath, "config.dat")
        try:
            configFileObject = open(configFileName, "rb")
            configData = self.xor(configFileObject.read()).decode("UTF-8")
            cfg = json.loads(configData)
            self.adminConfig = cfg
        except:
            print("Could not admin configuration")
            self.adminConfig = {}


    def saveConfig(self):
        # Save accounts
        configFileName = os.path.join(self.storagePath, "accounts.dat")
        configFileObject = open(configFileName, "w+b")
        configData = self.xor(json.dumps(self.accounts).encode("UTF-8"))
        configFileObject.write(configData)
        configFileObject.flush()
        configFileObject.close()
        #Save rest of the config
        configFileName = os.path.join(self.storagePath, "config.dat")
        configFileObject = open(configFileName, "w+b")
        configData = self.xor(json.dumps(self.adminConfig).encode("UTF-8"))
        configFileObject.write(configData)
        configFileObject.flush()
        configFileObject.close()

    def loadPortalConfig(self, url):
        print("------------------ LOADING PORTAL CONFIG -------------_")
        self.currentPortalConfigDirectory = os.path.join(self.storagePath, sha512(url.encode("UTF-8")).hexdigest())
        try:
            if not os.path.isdir(self.currentPortalConfigDirectory):
                os.mkdir(self.currentPortalConfigDirectory)
            configFileObject = open(os.path.join(self.currentPortalConfigDirectory, "config.dat"), "rb")
            configData = configFileObject.read().decode("UTF-8")
            cfg = json.loads(configData)
            self.portal = cfg
        except:
            print("Could not load Portalconfig")
            self.portal = {"modules": {}}

    def savePortalConfig(self):
        if not self.currentPortalConfigDirectory:
            return
        configFileObject = open(os.path.join(self.currentPortalConfigDirectory, "config.dat"), "w+b")
        configData = json.dumps(self.portal).encode("UTF-8")
        configFileObject.write(configData)
        configFileObject.flush()
        configFileObject.close()


conf = Config()


