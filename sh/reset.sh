#!/bin/bash

cd /home/dami/bot/sql;
psql postgres -f reset_extracciones.sql;
