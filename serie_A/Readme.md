# Serie A

![Serie A Logo](https://raw.githubusercontent.com/fede-chiodi/python/master/serie_A/serie-a-logo.jpg)

To use the program you need to create a virtual environment.
```bash
python3 -m venv .venv 
source .venv/bin/activate
pip install colorama requests
```

## 🔌HOW IT WORKS
The program is based on a multithreading paradigm which use the Producer-Consumer way to work. With this paradigm the Producer process the datas taken from a github repo and put them into a Queue, that is a sharable entity between the different Producer Thread.
After that, when all the Producers have finshed their work, start the Consumer Thread which allow the user to interact with the program, giving him the datas he want.
