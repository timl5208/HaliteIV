from kaggle_environments import evaluate, make

env = make("halite", configuration={ "episodeSteps": 400 }, debug=True)
steps = env.run(["submission.py", "random"])
print(steps)
out = env.render(mode="html", width=800, height=600)
f = open("replay.html", "w")
f.write(out)
f.close()