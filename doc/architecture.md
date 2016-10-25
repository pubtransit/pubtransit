# System Architecture Design

## Overview

The System Architecture is very simple: the Web page is static and doesn't relies on any running applicance.
This approch was decided to maximize the site scalability and semplicity. There is no dynamic data.
The public transit data is instead splitted in small compressed binary file (called here feed files)
and made available via HTTP or HTTPS protocol. The Web browser is in charge of searching by parsing an index
and download those files are required by the user.

![Data Flow](doc/data-flow.svg)
