import uvicorn

if __name__ == "__main__": # wonder if this line should be different since this file isn't called main. I think this just works when I call it from command line
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)