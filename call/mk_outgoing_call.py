import pjsua2 as pj
from utils import sleep4PJSUA2, handleErr
import traceback
import sys
import utils

import hydra
from omegaconf import DictConfig, OmegaConf

class Call(pj.Call):
    """
    Call class, High level Python Call object, derived from pjsua2's Call object.
    there are Call class reference: https://www.pjsip.org/pjsip/docs/html/classpj_1_1Call.htm
    We may wants to implement our Call object to handle the "outgoing" call implement logic
    """

    def __init__(self, acc, peer_uri='', chat=None, call_id=pj.PJSUA_INVALID_ID):
        pj.Call.__init__(self, acc, call_id)
        self.acc = acc
        self.wav_player = None

    # override the function at original parent class
    # parent class's function can be called by super().onCallState()
    def onCallState(self, prm):
        ci = self.getInfo()
        print("*** Call: {} [{}]".format(ci.remoteUri, ci.lastStatusCode))

    def onCallMediaState(self, prm):
        # Deprecated: for PJSIP version 2.8 or earlier
        # ci = self.getInfo()
        # for mi in ci.media:
        #     if mi.type == pj.PJMEDIA_TYPE_AUDIO and \
        #         (mi.status == pj.PJSUA_CALL_MEDIA_ACTIVE or
        #          mi.status == pj.PJSUA_CALL_MEDIA_REMOTE_HOLD):
        #         m = self.getMedia(mi.index)
        #         am = pj.AudioMedia.typecastFromMedia(m)
        #         # connect ports
        #         ep.Endpoint.instance.audDevManager().getCaptureDevMedia().startTransmit(am)
        #         am.startTransmit(
        #             ep.Endpoint.instance.audDevManager().getPlaybackDevMedia())
        aud_med = None
        try:
            # get the "local" media
            aud_med = self.getAudioMedia(-1)
        except pj.Error as e:
            handleErr(e)

        if not self.wav_player:
            self.wav_player = pj.AudioMediaPlayer()
            try:
                self.wav_player.createPlayer("/home/ahmed/work/aiIdea/pjsua2-test/AD-FinalCountdown_pt2.wav")
            except pj.Error as e:
                del self.wav_player
                self.wav_player = None
                handleErr(e)

        if self.wav_player:
            self.wav_player.startTransmit(aud_med)


def enumLocalMedia(ep):
    # important: the Endpoint::mediaEnumPorts2() and Call::getAudioMedia() only create a copy of device object
    # all memory should manage by developer
    print("enum the local media, and length is ".format(len(ep.mediaEnumPorts2())))
    for med in ep.mediaEnumPorts2():
        # media info ref: https://www.pjsip.org/pjsip/docs/html/structpj_1_1MediaFormatAudio.htm
        med_info = med.getPortInfo()
        print("id: {}, name: {}, format(channelCount): {}".format(
            med_info.portId, med_info.name, med_info.format.channelCount))


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg : DictConfig):
    ep = None
    try:
        # init the lib
        ep = pj.Endpoint()
        ep.libCreate()
        ep_cfg = pj.EpConfig()
        ep.libInit(ep_cfg)

        # add some config
        tcfg = pj.TransportConfig()
        # tcfg.port = 5060
        ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, tcfg)


        #add credentials
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


        acc = pj.Account()
        acc.create(acfg)

        ep.libStart()
        print("*** PJSUA2 STARTED ***")

        # use null device as conference bridge, instead of local sound card
        pj.Endpoint.instance().audDevManager().setNullDev()

        call = Call(acc)
        prm = pj.CallOpParam(True)
        prm.opt.audioCount = 1
        prm.opt.videoCount = 0
        call.makeCall(idUri, prm)

        # hangup all call after 40 sec
        sleep4PJSUA2(10)

        print("*** PJSUA2 SHUTTING DOWN ***")
        del call
        del acc

    except KeyboardInterrupt as e:
        print("Catch the KeyboardInterrupt, exception error is: {}".format(e.args))

    # close the library
    try:
        ep.libDestroy()
    except pj.Error as e:
        handleErr(e)


if __name__ == '__main__':
    main()
