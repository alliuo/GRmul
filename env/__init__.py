from gym.envs.registration import register

ENV_ID = 'multiplier_env-v0'

register(
    id=ENV_ID,
    entry_point='env.multiplier_env:MultiplierEnv'
)
