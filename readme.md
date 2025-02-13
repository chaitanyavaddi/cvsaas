
# CVSAAS Boilerplate Repository

This repository is a SaaS boilerplate code built with HTMX, FastAPI, Jinja2, and Supabase. This template is authentication-ready, allowing users to sign up, log in, reset passwords, and access the dashboard. The UI is designed using Preline components (opensource).



## Tech Stack

**Client:** Preline UI, HTMX, JINJA2, TailwindCSS

**Server:** Python, FASTAPI

**DB:** Supabase


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file. Login to your supabase account and copy the Project URL & Project Key.

`SUPABASE_URL`

`SUPABASE_KEY`


# To Run Locally
### Prerequisites

- Python 3.7 or higher
- pip

### Steps
1. Clone the project

```bash
  git clone https://github.com/chaitanyavaddi/cvsaas.git
```

2. Go to the project directory

```bash
  cd cvsaas
```

3. Install dependencies

```bash
  pip install -r requirements.txt
```

4. Start the server

```bash
  fastapi dev
```

### Running Tailwind Build 

5. Open a New Terminal and change to the tailwindcss directory

```bash
  cd tailwindcss
```

6. Run the tailwind build command

```bash
  ./tailwindcss -i ./input.css -o ../static/output.css --watch
```

7. Add 'tailwindcss' to the .gitignore file. We don't need to commit the tailwindcss folder, as it only contains the standalone .exe, config, and input.css file. The command in step 6 will automatically export the required css file (output.css) to the static folder at the root directory.

### Structure
```app/```: App modules \
- ```auth```
- ```users```
- ```dashboard```

```templates/```: HTML \
```static/```: CSS, JS \
```tailwindcss/```: Tailwind config, build
## Authors

- [@chaitanyavaddi](https://www.github.com/chaitanyavaddi)


## Setting Up Framework From Scratch

Installing Python, and requirements using pip is all same.

I'd like to write about how I did setup tailwind for the first time.

### Notes

- Download Tailwind standalone v3 ```.exe``` from https://github.com/tailwindlabs/tailwindcss/releases/tag/v3.4.16
- Create folder at root with name - ```tailwindcss``` and put the file inside
- Rename the ```.exe``` to ```tailwindcss```
- Open new terminal, cd tailwindcss
- Run ```./tailwindcss init``` (This will create ```tailwind.config.json```)
- Update tailwind.config.js ```content: ["../templates/**/*.{html, js}"]```
- Run ```./tailwindcss -i ./input.css -o ../static/output.css --watch```
- A new ```output.css``` will be created inside ```static``` folder at root
- Now we can add ```tailwindcss``` to ```.gitignore```

Note: Why only v3? cos' from v4 ```./tailwind init``` command wont work. And we are using tailwind standalone .exe file. So we need not install node & npm in the system. We get tailwind features working in HTML out of the box. Only thing is once the output.css file is genrated, we will mount it to our app in ```main.py``` using fastapi ```app.mount()``` 