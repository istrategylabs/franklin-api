# franklin

Now with Github deploys!

![franklin](http://www.brand-licensing.com/DBImages/lizenzen/franklin-logo.jpg)

## Installation

1. Install [docker toolbox](https://www.docker.com/toolbox)
1. Initialize your docker machine system if you have not already: `docker-machine start default`
1. Run our startup script: `. ./scripts/setup.sh`
1. In a new shell run `docker-machine ip default` to find out the IP address of your container
1. Visit site at `<my-ip>:5000`
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
      API_BASE_URL=<franklin_api_url>
      SOCIAL_AUTH_GITHUB_KEY=<github_client_id>
      SOCIAL_AUTH_GITHUB_SECRET=<github_client_secret>
    ```
- Projects you wish to be deployed by franklin will need a `.franklin` file in their root

  ```
    TODO - add example build/deploy settings here.
    Note - Environment configuration will likely be handled during the registration step. So not here.
  ```

## Making Changes to the Code

- If your code change includes a new requirement, you will likely have to run `docker-compose build`. This will re-run the build step which will include a pip install of all requirements.

## Testing

###ngrok: 

1. Install [ngrok](https://ngrok.com/)
1. Start `franklin-api` (See Installation above)
1. From the ngrok install location, run `ngrok http <my-ip>:[port-for-franklin]`
1. ngrok will tell you the endpoint you can hit
1. You're endpoint will be something like `http://b551e0ad.ngrok.io/deployed`
1. You'll know it's working as ngrok will log http status codes for every request
1. Test it by dropping the url in any web browser on any computer. The response and ngrok server logs should record a rejected GET request on an endpoint that only accepts POST.
1. Bonus: You can also do the above for [franklin-build](https://github.com/istrategylabs/franklin-build), and use the ngrok endpoint as your `BUILDER_URL` and `API_BASE_URL` in your `.env`. Do this before starting `franklin-api`. ngrok can manage both endpoints at the same time. You could also point your local `franklin-api` to your test environment for `franklin-build`. Thus, you'll be working with production ready code while you prototype your changes here. 

### Configure Github Social Signin
1. Create a personal application for testing github's api. [github settings](https://github.com/settings/applications)
1. The callback URL should look something like `http://192.168.99.100:5000/complete/github`
1. Make sure there is no trailing slash on the callback URL
1. Set the `Client ID` and `Client Secret` in your config above

### Configure an oAuth application for franklin
1. create a superuser `docker-compose run web python manage.py createsuperuser`
1. Login as super user as `http://192.168.99.100:5000/admin/`
1. Navigate to `Oauth2_Provider --> Applications --> Add Application +`
1. `user` -> superuser
1. `Client Type` -> `Confidential`
1. `Authorization Grant Type` -> `Resource Owner password-based`
1. Save the `client id` and `client secret`

### Obtain a Github OAuth Token
1. Log into Github
1. Navigate to `Settings --> Personal Access Tokens --> Generate New Token`
1. Use the default permissions.
1. You will need to save the token as you will not be able to read it again. (regenerating it is easy though)

### Login/Create account with the api using Github oAuth creds above
1. Make a POST call the api convert token endpoint. e.g. `http://192.168.99.100:5000/auth/convert-token/`
1. Body type must be `x-www-form-urlencoded`
1. Key/Values in body:
1. `grant_type` -> `convert_token`
1. `client_id` -> <client-id-from-superuser-admin-step>
1. `client_secret` -> <client-secret-from-superuser-admin-step>
1. `token` -> <token-from-github-step>
1. `backend` -> `github`
1. If successful, you should have a payload like below. All regular api calls
   will require the `access_token` in the header to succeed. At this point you
   should also observe that your github user is in the database and properly
   linked to the social auth model.

   ```
    {
        "access_token": "hNns5FjUxI9b613djPH6xqr4IaJvgM",
        "expires_in": 36000,
        "scope": "write read",
        "token_type": "Bearer",
        "refresh_token": "miE4TgZY19CggeRx8adaroVSPIIBwU"
    }
   ```

### Register one of your projects
1. The project must have a `.franklin` file in it's root (see above)
1. You will make a POST call the api registration endpoint. e.g. `http://192.168.99.100:5000/register/`
1. Header: `Authorization` -> `Bearer <access_token>`
1. Body:

  ```
  {
    "name": "my_project",
    "github_id": 123456,
    "owner": {
        "name": "istrategylabs",
        "github_id": 607333
    }
  }
  ```
1. create a superuser by running `docker-compose run web python manage.py createsuperuser`
1. Log into the admin at `http://192.168.99.100:5000/admin/`
1. Confirm that your test project is there with all relevant info
1. Log into github and navigate to: `settings > Webhooks & services`
1. Confirm that a webhook has been created and has a green check mark next to it
1. You may need to delete the webhook periodically for testing purposes

### Debugging Github Webhooks:
1. These steps are useful for rapidly testing the deployment endpoint without actually pushing code.
1. Start at the url for your test project's repo (e.g. `https://github.com/istrategylabs/franklin-api`)
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
