![PACSnPULL Title](https://github.com/jacobmatthewmurray/pacsnpull/blob/master/pacsnpull.png)

# pacs n pull (prototype) 

pacs n pull (prototype) is a dockerized python utility for bulk interaction with picture archiving and communication systems 
(PACS). the aim is to drastically simplify the process of assembling large-scale data sets for medical imaging research.
to this end, pacs n pull provides an easy-to-use user interface and a command line utility for scripting.


### getting started
1. install docker
2. build image from github  `docker build -t pacsnpull:latest https://github.com/jacobmatthewmurray/pacsnpull.git#:docker` or clone repository and build locally
3. run pacsnpull through the ui or command line (see below)
4. in configuration menu enter your configuration details (see below for an example). then test connection to PACS via echo.
5. upload a query in query menu. this query MUST BE a .json file of the form `[{"DicomField":"Value", "DicomField": "*", ...}, ...., {"DicomField":"Value", "DicomField": "*", ...}]`. it MUST include the DICOM Tag "QueryRetrieveLevel", which can take the values "STUDY" or "PATIENT". 
6. execute the find or move for the query. note that the query elements available for find and move queries might differ. if you run a move query with the intention of moving dicom files to your local machine, remember to activate a store in the store menu.

### queries
queries for upload must take the json format
```
[
    {
    "DicomField":"Value", 
    "DicomField": "*", 
    ...
    }, 
    ...., 
    {
    "DicomField":"Value", 
    "DicomField": "*",
    ...
    }
]
```
queries must include the field "QueryRetrieveLevel", which can be set to "STUDY" or "PATIENT".


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

note that docker networking differs between operating system. the command below works on Ubuntu. also note that depending on your configurations you might not want to use the network host option. in that case, map ports using the docker port mapping and run the flask app on the specified port. 

all the downloaded information, as well as the query information is stored on disk (see below re: design choices). hence, map a volume from your host machine. in the below examples, the directory "~/storedir" is being mapped.


if running with --network="host":
```
docker run --network="host" -v ~/storedir:/pacsnpull/instance --rm  pacsnpull flask run
```
if running with port mapping (preferred): 
```
docker run -p 5050:5050 -v ~/storedir:/pacsnpull/instance --rm  pacsnpull:latest flask run --port=5050 --host=0.0.0.0
```

### pacs n pull from the command line
below examples shows how to run a move query through the command line. again a store directory needs to be mapped. in addition a configuration file must be mapped as well as a query file. configuration and query files always map to the same destinations, that is, to `/pacsnpull/instance/cli/conf.json` and `/pacsnpull/instance/cli/move.json` or `/pacsnpull/instance/cli/find.json`. 

```
docker run --network="host" -v ~/storedir:/pacsnpull/instance \
-v ~/projects/pacsnpull/instance/config.json:/pacsnpull/instance/cli/conf.json:ro \ 
-v ~/projects/pacsnpull/instance/move_query_single.json:/pacsnpull/instance/cli/move.json --rm  pacsnpull flask move
```

### some design comments
the initial idea was to build pacs n pull as simple and lightweight as possible. in that sense, no database was added to store information. all queries are written to disk, all results are too. this means that meta data, like query status or the query file is held in the browser during each query. this might change in the future with the addition of a lightweight db. 

currently, the UI - especially feedback to the user on whether the find/move is running - is not optimal. (after initial click on move/find, until first query is completed, the status bar does not update or show that query is in progress.) this will be improved.

pacs n pull relies on background processes that retrieve and report information (like query status). this information is currently compiled in the background on the server-side for each query and then sent to the client. this was done to keep things simple -- but it has issues: 1. concurrency 2. keeping user informed during long queries. ideally, background processes would be queued (i.e., redis - which would also solve concurrency issues) and sent to the PACS at admin-defined rate. also, status from background processes should be reported in real-time to user (i.e., HTML5 stream/ websockets). these adjustments are in the works. 


### faq
### building a testing environment
