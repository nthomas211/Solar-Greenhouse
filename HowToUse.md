# How To Connect and Run:


This project is a local web-based greenhouse simulation that uses a Python backend and a Vite-powered frontend. To run the application successfully, both the backend and frontend must be started in separate terminal windows.

---

## Prerequisites

Before running the project, make sure the following are installed on your system:

- [Git](https://git-scm.com/)
- [Python](https://www.python.org/)
- [Node.js and npm](https://nodejs.org/)

you could also download these by running these commands in the terminal: 

```bash
winget install --id OpenJS.NodeJS.LTS 
winget install --id Python.Python.3.13
winget install --id Git.Git -e --source winget

```

You may also want to verify that these are available in your terminal by typing this :

```bash
git --version
python --version
npm --version 
```

After installing these on your machine, first clone the repository to your local machine by opening up the terminal and running this command in your preferred directory:

```bash
git clone https://github.com/nthomas211/Solar-Greenhouse.git
```

## Backend Setup

The backend must be started first so the frontend can communicate with it.

1. Navigate to the backend folder from the main folder of the Solar-Greenhouse Repository 

```bash
cd backend
```
Once you are in the backend, it should look something like this:

```bash
C:\Users\<name>\<folder>\Solar-Greenhouse\backend>
```
Next, run the command:

```bash
pip install -r requirements.txt
```
After that has finished, start the backend server by running:

```bash 
python main.py
```
### Once this command is running, leave that terminal open. The backend needs to stay active while using the simulator.

## Frontend

Next, open another terminal window or a new tab in the terminal and navigate into the main Solar-Greenhouse folder again and connect to the frontend using: 


```bash
 cd frontend/greenhouse-simulation-app
```
Once you are in the frontend, it should look something like this: 
```bash
C:\Users\<name>\<folder>\Solar-Greenhouse\frontend\greenhouse-simulation-app
```
Now install frontend dependencies using the command:
```bash
npm install
```

Now start the Vite development server with the command:
```bash
npm run dev
```

After running this command, the terminal will display a local development URL, usually something like:

"http://localhost:5173/"

# Troubleshooting
### pip is not recognized

This usually means Python is either not installed or not added to your system PATH.

### npm is not recognized

This usually means Node.js is not installed or not added to your system PATH. or if your computer prevents running scripts on your device you could run this command:

`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`


### Frontend opens but does not work correctly

Make sure the backend is still running in the other terminal.

### npm install or pip install fails

Check that you are in the correct folder before running the command.

requirements.txt should be run inside the backend folder
npm install should be run inside frontend/greenhouse-simulation-app

If the localhost link does not open, copy the exact URL shown after running npm run dev and paste it directly into your browser.
