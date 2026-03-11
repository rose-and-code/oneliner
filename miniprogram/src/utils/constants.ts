import developEnv from '../config/env.develop'
import trialEnv from '../config/env.trial'
import releaseEnv from '../config/env.release'

const envVersion = wx.getAccountInfoSync().miniProgram.envVersion || 'develop'
const env = { develop: developEnv, trial: trialEnv, release: releaseEnv }[envVersion] || developEnv

export const API_BASE = env.API_BASE

export const SWIPE_THRESHOLD = 36
export const SWIPE_MAX_TIME = 300
export const TAP_MAX_DISTANCE = 12
export const GESTURE_THROTTLE_MS = 400
export const FLIP_DURATION_MS = 650
