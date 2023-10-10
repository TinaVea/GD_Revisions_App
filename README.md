# GD_Revisions_App

# GD_Revisions_HTML


![GD Rvisions HTML](https://media.makeameme.org/created/revisions-revisions-everywhere.jpg)

- Usage:

<h2>Step 1: Create a New Project in Google Developers Console</h2>


Go to Google Developers Console.
- Click on the "Select a project" dropdown, then click on the "New Project" button.
- Enter a name for your project and select a billing account (if you have one).
- Click on the "Create" button.

<h2>Step 2: Enable Google Drive API</h2>

- In your new project, navigate to the "Dashboard" on the left-hand side.
- Click on the "+ ENABLE APIS AND SERVICES" button.
- In the search bar, type "Google Drive" and select "Google Drive API".
- Click the "Enable" button on the next page.

<h2>Step 3: Create OAuth 2.0 Credentials</h2>
- Click on "Create credentials" and select "OAuth client ID".
- Select "Desktop app" for the application type and enter a name for your OAuth client ID.
- Click on "Create".
- Click on the download icon (down arrow) next to your new credentials and save the file as "credentials.json".

<h2>Step 4: Install Required Python Packages</h2>

- Open a terminal and navigate to the directory where you saved your "credentials.json" file.
- Run the following commands to install the necessary packages:

```pip install flask pandas google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 oauth2client```

<h2>Step 5: Run the Python Script</h2>

- In your terminal, navigate to the directory containing your "credentials.json" and "app.py" files.

```python app.py```
- Open a web browser and navigate to http://localhost:5000/.
- You will be prompted to authorize the app to access your Google Drive. Follow the steps to grant permission.


<h2>Step 6: View the Generated HTML Page</h2>

- After you've authorized the app, the HTML page will be generated and displayed in your browser.
- You will see a summary of the folder structure and revisions of the files in your Google Drive.

