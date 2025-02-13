
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
4. In New Terminal

```bash
   cd tailwindcss
```

5. Install dependencies

```bash
   npm i
```

6. If you see 0 vulnerabilities, start the build

```bash
   npm run build
```
7. In another terminal, start the server

```bash
  fastapi dev
```

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

The above setup should keep the boilerplate working. 

## Method 1: Setting Up Framework From Scratch

Installing Python, and requirements using pip is all same.

I'd like to keep a note for myself on about how I did setup all of this for the first time.

### Notes

1. Create tailwindcss folder for local build process
```bash
  mkdir tailwindcss
  cd tailwindcss
  npm init -y
  npm install -D tailwindcss@3.4.1
  npx tailwindcss init
  npm install -D @tailwindcss/forms 
```
2. Add preline & tailwind forms plugins inside tailwind.config.js

```bash
  require('preline/plugin')
  require('@tailwindcss/forms')
```

3. Copy preline.js from nodemodules/preline/preline.js to static/js

```bash
  cp tailwindcss/node_modules/preline/dist/preline.js static/js/
```
3. Update 'content' inside tailwind.config.js as below
```bash
content: [
    "../templates/**/*.{html, js}",
    'node_modules/preline/dist/*.js',
    '../static/js/*.js',
  ],
```

The final tailwind config should look like:
```
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "../templates/**/*.{html, js}",
    'node_modules/preline/dist/*.js',
    '../static/js/*.js',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('preline/plugin'),
  ],
}
```
### Method 2: To do it with tailwind exe file:
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