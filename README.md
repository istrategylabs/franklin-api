# franklin

Now with Github deploys!

![franklin](http://www.brand-licensing.com/DBImages/lizenzen/franklin-logo.jpg)

## Installation

1. Install [docker toolbox](https://www.docker.com/toolbox)
1. Initialize your docker machine system if you have not already: `docker-machine start default`
1. Run our startup script: `. ./scripts/setup.sh`
1. In a new shell run `docker-machine ip default` to find out the IP address of your container
1. Visit site at `<my-ip>:8000`
1. Run commands inside the container like such: `docker-compose run web python manage.py migrate`

## Other Considerations

- You will need a `.env` file in the root of your project that defines the following keys:


    ```
      CLIENT_ID=<github_client_id>
      CLIENT_SECRET=<github_client_secret>
      BASE_PROJECT_PATH=~/Desktop
      DJANGO_SETTINGS_MODULE=config.settings.local
      BASE_URL=franklinstatic.com
      SECRET_KEY=<your_secret_key>
      BUILDER_URL=<franklin_builder_url>
      ENV='local'
      GITHUB_OAUTH=<github_oauth_token>
    ```

## Making Changes to the Code

- If your code change includes a new requirement, you will likely have to run `docker-compose build`. This will re-run the build step which will include a pip install of all requirements.

## Testing

###ngrok: 

1. Install [ngrok](https://ngrok.com/)
1. Start franklin-build
1. From the ngrok install location, run `ngrok http [port-for-franklin]`
1. ngrok will tell you the endpoint you can hit
1. You're endpoint will be something like `http://b551e0ad.ngrok.io/deployed`
1. You'll know it's working as ngrok will log http status codes for every request

### Github Webhooks: 
1. Start at the url for your test projects repo e.g. `https://github.com/istrategylabs/franklin-api`
1. Go to `settings > Webhooks & services > Add webhook`
1. The url should be the url supplied by `ngrok` above, ending with our endpoint /deployed
1. Leave all other defaults unless you've enabled security on the endpoint.

### What a github Webhook looks like:
- If you are testing the api with a tool like [postman](https://www.getpostman.com/), you will want to properly replicate the important payload information the api receives from Github.
- Headers: "X-Github-Event": "push" and "Content-Type": "application/json"
- Body: 

  ```
  {
    "head_commit": {
      "id": "218d7af49c73e8654ea18356e3c6283b3c8d701a"
    },
    "repository": {
      "full_name": "istrategylabs/franklin-build"
    }
  }
  ```

### Obtain a Github OAuth Token
1. Log into Github
1. Navigate to `Settings --> Personal Access Tokens --> Generate New Token`
1. Use the default permissions.
1. You will need to save the token as you will not be able to read it again. (regenerating it is easy though)
1. Add it as `GITHUB_OAUTH` to the config file detailed above.
