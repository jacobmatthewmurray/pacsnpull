# pacs n pull

pacs n pull is a dockerized python utility for bulk interaction with picture archiving and communication systems 
(PACS). the aim is to drastically simplify the process of assembling large-scale data sets for medical imaging research.
to this end, pacs n pull provides an easy-to-use user interface and a command line utility for scripting.


### getting started
1. docker installation 


### queries

### configuration
the basic configuration options for pacs n pull, which can also be entered through the ui, are shown below. for command
line usage, this should be the format of the config file. for ui usage, these fields can be entered directly. 

```
{
    "job_title": "cmdline",
    "host_ip": "127.0.0.1",
    "host_port": 4242,
    "client_name": "STORESCP",
    "client_ip": "",
    "client_port": 2000,
    "query_model": "S",
    "query_break_count": 10
}
```

### pacs n pull through the ui

```
docker run --network="host" -v ~/storedir:/pacsnpull/instance --rm  pacsnpull flask run
```

### pacs n pull from the command line

```
docker run --network="host" -v ~/storedir:/pacsnpull/instance \
-v ~/projects/pacsnpull/instance/config.json:/pacsnpull/instance/cli/conf.json:ro \ 
-v ~/projects/pacsnpull/instance/move_query_single.json:/pacsnpull/instance/cli/move.json --rm  pacsnpull flask move
```

### faq


### building a testing environment