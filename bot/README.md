# Introduction 

This folder contains the source code of our drifter bots.

All parameters are in the file `config_stats.py`

Each drifter is activated by executing `python drifter_main.py <DRIFTER_HANDLE>`. This script will periodically activate and execute some actions, then sleep until the next activation. The script will also be inactive during a "night" period specified by the `activation_time` parameter. It is a good idea to periodically check if the drifters are running properly.

The following figure shows the behavior model of the drifters:

![Bot Behaviour Workflow](/exps/images_out/drifter_bot_behavior.png)
