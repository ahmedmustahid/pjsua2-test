#!/usr/bin/env python3

import sys
import os
import logging
import pjsua2 as pj

import hydra
from omegaconf import DictConfig, OmegaConf

# ep = pj.Endpoint()
ep = None

class Call(pj.Call):
    def __init__(self, acc, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.call_state = None

    def onCallState(self, prm):
        """
        typedef enum pjsip_inv_state
        {
            PJSIP_INV_STATE_NULL,        /**< Before INVITE is sent or received  */
            PJSIP_INV_STATE_CALLING,        /**< After INVITE is sent            */
            PJSIP_INV_STATE_INCOMING,        /**< After INVITE is received.        */
            PJSIP_INV_STATE_EARLY,        /**< After response with To tag.        */
            PJSIP_INV_STATE_CONNECTING,        /**< After 2xx is sent/received.        */
            PJSIP_INV_STATE_CONFIRMED,        /**< After ACK is sent/received.        */
            PJSIP_INV_STATE_DISCONNECTED,   /**< Session is terminated.            */
        } pjsip_inv_state;
        """
        ci = self.getInfo()
        logging.debug("Call state: {}".format(ci.state))
        logging.debug("Call stateText: {}".format(ci.stateText))
        # save call state to some class var
        self.call_state = ci.state

        # playing the wav file
        # create the AudioMediaPlayer
        # aud_med = self.getAudioMedia(-1)
        # play_dev_med = ep.instance().audDevManager().getPlaybackDevMedia()
        play_dev_med = pj.Endpoint.instance().audDevManager().getPlaybackDevMedia()
        print(play_dev_med)
        player = pj.AudioMediaPlayer()
        player.createPlayer("/home/efficacy38/Tmp/pjsua2/media/test.wav", pj.PJMEDIA_FILE_NO_LOOP)
        # player.createPlayer("/home/efficacy38/test.wav")
        player.startTransmit(play_dev_med)


class Account(pj.Account):
    def __init__(self):
        super().__init__()

@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg : DictConfig):
    print(OmegaConf.to_yaml(cfg))

    # Create and initialize the library
    global ep
    ep_cfg = pj.EpConfig()

    ep_cfg.uaConfig.threadCnt = 0
    ep_cfg.uaConfig.mainThreadOnly = True

    ep_cfg.logConfig.level = 5
    ep_cfg.logConfig.consoleLevel = 5

    ep = pj.Endpoint()
    ep.libCreate()
    ep.libInit(ep_cfg)
    # ep.audDevManager().setNullDev()

    # Create SIP transport. Error handling sample is shown
    sipTpConfig = pj.TransportConfig()
    ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sipTpConfig)

    # Start the library
    ep.libStart()

    sipServerIP = cfg.sipServer.ip 
    sipServerPort = cfg.sipServer.port
    sipServerUsername = cfg.sipServer.username
    sipServerPassword = cfg.sipServer.password 
    acfg = pj.AccountConfig()
    idUri = "sip:"+sipServerUsername+"@"+sipServerIP+":"+str(sipServerPort)
    print(f"sending request to {idUri}")
    acfg.idUri = idUri
    cred = pj.AuthCredInfo("digest", "*", sipServerUsername, 0, sipServerPassword)
    acfg.sipConfig.authCreds.append(cred)


    # Create the account
    acc = Account()
    acc.create(acfg)

    ep.audDevManager().setNullDev()
    call = Call(acc)
    call_param = pj.CallOpParam()
    call_param.opt.audioCount = 1
    call_param.opt.videoCount = 0
    call_prm = pj.CallOpParam(True)
    call.makeCall(idUri , call_prm)

    # while not call.done:
    while True:
        ep.libHandleEvents(10)
        # check your saved call_state here
        if not call.call_state:
            continue
        if call.call_state == pj.PJSIP_INV_STATE_CONFIRMED:
            call.done = True

    # Destroy the library
    ep.libDestroy()


if __name__ == "__main__":
    main()
