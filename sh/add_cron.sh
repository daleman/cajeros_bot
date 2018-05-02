#!/bin/bash

# Todos los dias a las 8 de la manana ejecutar reset
line="* 8 * * * /home/dami/bot/sh/reset.sh"
(crontab -u dami -l; echo "$line" ) | crontab -u dami -