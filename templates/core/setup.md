# Messenger Setup Guide

This guide will walk you through creating and connecting a Messenger app to your server so you can receive and send messages through Facebook Messenger.

---

## 1. Create a Facebook App

1. Go to [Facebook for Developers](https://developer.facebook.com/).
2. Click **My Apps** → **Create App**.
3. Fill in:

   * **App name**
   * **Contact email**
4. Select:

   * **Other** → **Business**
5. Click **Create App**.

---

## 2. Set Up Webhook URL

Messenger uses a webhook to send you messages from your page.

1. Inside your app dashboard, click **Set Up** under **Messenger**.
2. Enter:

   * **Callback URL**:

     ```
     https://chatautopilot.net/username/webhook/m
     ```
   * **Verify Token** (a password you choose):

     ```
     verify-token
     ```
3. Save changes.

---

## 3. Generate Page Access Token

To reply to messages, you need a **Page Access Token**.

1. Click **Connect**.
2. Continue as your Facebook account.
3. Select the **Page** you want to connect.
4. Continue and confirm.
5. Under **Subscriptions**, check:

   * `messages`
   * `messaging_postback`
6. Confirm your choices.
7. Go to **Token** → **Generate**.
   Copy the generated token (this works like a password with permissions).

---

## 4. Test the Connection

1. Send a message from the Facebook account you connected earlier.
2. Your server should receive the message and send an automatic reply.

⚠️ At this stage, it will **only work with your own account**. To enable it for all users, continue to the next step.

---

## 5. Make the App Live

To allow messages from any user, you must make the app public.

1. Prepare a **Privacy Policy URL** (this can be a simple page explaining how you handle data).
2. In the app dashboard, go to **App Settings → Basic**.
3. Paste your privacy policy URL into the **Privacy Policy URL** field.
4. Click **Save Changes**.
5. Toggle the **App Mode** switch to **Live**.

Now your Messenger bot is live and will respond to messages from all users.

---

✅ Done! Your Messenger app is now connected and live.

### Notes & Tips

* Keep your **Verify Token** and **Page Access Token** secret.
* Tokens may expire; regenerate them if your bot stops responding.
* Always test with multiple accounts after going live.
* Facebook requires apps to follow its [Platform Policies](https://developers.facebook.com/policy/).
