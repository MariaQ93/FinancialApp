
https://github.com/user-attachments/assets/7ae58898-a6ea-46f7-b832-1b7c13d19857

# PetHood Financial App

This is a financial app that allows users to practice buying and selling stocks in a simulated stock market environment. It features various pages to manage and track investments, including stocks, transactions, and overall portfolio performance.

## Features

### 1. **Login Page**
![WeChat41f4512ba1d309ee854d5a54a50f4008](https://github.com/user-attachments/assets/4e74c432-27fe-46ea-b621-c7600920a7c4)

   - Users can register for a new account or log in to an existing account.
   - After logging in, users gain access to the app's core features, including stock tracking, portfolio management, and transaction history.


### 2. **Dashboard**
![WeChat663e8a087604618359c91b3c90e184ff](https://github.com/user-attachments/assets/7c8e1a1c-741b-479b-ae78-f80dfce5bd94)

   - Provides an overview of all user activities, including portfolio value, total assets, and stocks added to the watchlist.
   - Users can get a snapshot of their investments and performance on this page.

### 3. **Portfolio**
![WeChate095a769b42e14ffaa1267880aefbeeb](https://github.com/user-attachments/assets/cae790e8-0794-40ad-8465-366d6b751c85)

   - Shows the user's total balance and tracks how much money has been earned or lost through investments.
   - A chart helps users visualize the total asset value over time.

### 4. **My Stock**
![WeChat590cf88adcc9fb8abafc7bb4241c3b98](https://github.com/user-attachments/assets/888a7716-93f5-4bf2-baec-32175df4b7d4)

   - A dedicated page to track the stocks that users have purchased, including the number of shares, current price per share, and overall value.
   - Users can also view a detailed transaction history of all stock buys and sells.

### 5. **Stock Market**
![WeChat147e7df81a811df50886a50b293c178b](https://github.com/user-attachments/assets/dcbbe841-6c5c-4a8c-9e3c-b44ff7cfd0c4)

   - Users can browse stocks, select specific stocks to buy or sell, and add stocks to their watchlist for future reference.
   - Stocks are organized by sectors to help users explore different markets easily.

## Running the Project

To run this project locally, follow these steps:

### 1. **Install Dependencies**
   - Navigate to the `frontend` folder.
   - Make sure you have `npm` installed. Then install the frontend dependencies by running the following command in the terminal:
     ```bash
     npm install
     ```
   - Next, navigate to the `backend` folder and install the required Python dependencies by running:
     ```bash
     pip install -r requirements.txt
     ```

### 2. **Running the Backend**
   - Open the first terminal window (or a new tab in terminal) and navigate to the `backend` folder.
   - Start the backend server by running:
     ```bash
     python app.py
     ```
   - This will start the backend server, which handles the logic and data processing for the app.

### 3. **Running the Frontend**
   - Open another terminal window (or another tab in terminal) and navigate to the `frontend` folder.
   - Start the frontend development server by running:
     ```bash
     npm start
     ```
   - This will launch the app in your default web browser at `http://localhost:3000`. The frontend provides the user interface where you can interact with the stock market simulation.

### 4. **Accessing the App**
   - After running both the frontend and backend servers, you can visit the application in your browser at `http://localhost:3000`.
   - From there, you can register for an account, log in, and start exploring the app's features.

## Technologies Used
- **Frontend**: React.js
- **Backend**: Python Flask
- **Data Visualization**: Charts are rendered using Chart.js to provide dynamic updates on stock prices and portfolio performance.

