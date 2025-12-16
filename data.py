import pandas as pd
import random

# 1. Load Data
df = pd.read_csv('udemy_courses.csv')

questions = []
answers = []

# --- A. Course-Specific Questions (The Core Data) ---
# We keep the "smart" questions generated previously
for index, row in df.iterrows():
    title = str(row['course_title']).strip()
    price = row['price']
    is_paid = row['is_paid']
    duration = row['content_duration']
    level = row['level']
    subject = row['subject']
    subscribers = row['num_subscribers']
    lectures = row['num_lectures']
    url = row['url']
    
    # 1. Price & Availability
    questions.append(f"How much does '{title}' cost?")
    questions.append(f"What is the price of '{title}'?")
    answers.append(f"The price is {price}." if is_paid else "It is free.")
    answers.append(f"It costs {price}." if is_paid else "This course is free.")

    # 2. Duration & Content
    questions.append(f"How long is '{title}'?")
    questions.append(f"What is the duration of '{title}'?")
    answers.append(f"It is {duration} hours long.")
    answers.append(f"The content duration is {duration} hours.")

    questions.append(f"How many lectures in '{title}'?")
    answers.append(f"It has {lectures} lectures.")

    # 3. Level & Suitability
    questions.append(f"Is '{title}' for beginners?")
    if level in ['Beginner Level', 'All Levels']:
        answers.append(f"Yes, it is rated as {level}, making it suitable for beginners.")
    else:
        answers.append(f"It is rated as {level}, so check if you meet the prerequisites.")
    
    questions.append(f"What is the difficulty of '{title}'?")
    answers.append(f"The difficulty level is {level}.")

    # 4. Access
    questions.append(f"Where can I buy '{title}'?")
    questions.append(f"Give me the link for '{title}'")
    answers.append(f"You can find it here: {url}")
    answers.append(f"Here is the link: {url}")

    # 5. Subject
    questions.append(f"What is '{title}' about?")
    answers.append(f"It is a course on {subject}.")

# --- B. Subject Aggregation (Intents) ---
subjects = df['subject'].unique()
for sub in subjects:
    sub_df = df[df['subject'] == sub].sort_values(by='num_subscribers', ascending=False).head(20)
    course_list = sub_df['course_title'].tolist()
    
    # Varied patterns for the same intent
    patterns = [
        f"I want to learn {sub}",
        f"Show me {sub} courses",
        f"Top courses in {sub}",
        f"List {sub} courses",
        f"What {sub} courses do you have?",
        f"Recommend {sub} courses"
    ]
    response_str = f"Here are our top recommended courses for {sub}: {course_list}"
    
    for pat in patterns:
        questions.append(pat)
        answers.append(response_str)

# --- C. EXPANDED General / Basic Questions ---

general_qa_categories = {
    "Account & Login": [
        ("I forgot my password", "Click on 'Forgot Password' at the login screen, enter your email, and we will send you a reset link."),
        ("How do I sign up?", "Click the 'Sign Up' button in the top right corner and enter your name, email, and password."),
        ("Can I change my email address?", "Yes, go to your Account Settings to update your email address."),
        ("How do I delete my account?", "You can close your account from the Profile Settings page. Warning: This is permanent."),
        ("I can't log in", "Check your email and password. If the issue persists, try resetting your password or contact support."),
        ("Is my account secure?", "Yes, we use industry-standard encryption to protect your data."),
        ("Can I merge two accounts?", "Unfortunately, accounts cannot be merged. Please choose one to use primarily.")
    ],
    "Payments & Refunds": [
        ("What payment methods do you accept?", "We accept Visa, MasterCard, Amex, PayPal, and various local payment options."),
        ("Is it a one-time payment?", "Yes, for most courses it is a one-time fee for lifetime access."),
        ("Do you offer refunds?", "Yes, we have a 30-day money-back guarantee for all eligible courses."),
        ("How do I request a refund?", "Go to your Purchase History, find the course, and select 'Request Refund'."),
        ("Can I pay in my local currency?", "Prices are usually displayed in your local currency based on your location."),
        ("Do you have coupons?", "Instructors often provide coupons. You can also check our homepage for seasonal sales."),
        ("How do I apply a coupon?", "Enter the coupon code in the 'Apply Coupon' box at checkout."),
        ("Can I gift a course?", "Yes! Click 'Gift this Course' on the course landing page and enter the recipient's email.")
    ],
    "Learning Experience": [
        ("How do I start a course?", "Once purchased, go to 'My Learning' and click on the course to start watching."),
        ("Can I download videos?", "Yes, if you use our mobile app, you can download lectures for offline viewing."),
        ("Are there quizzes?", "Most courses contain quizzes to help you test your understanding."),
        ("What happens if I fail a quiz?", "Don't worry! You can retake quizzes as many times as you need."),
        ("Do I have lifetime access?", "Yes! Once you buy a course, you own it forever."),
        ("Can I watch on my phone?", "Yes, download our app for iOS or Android to learn on the go."),
        ("Is there a deadline to finish?", "No, there are no deadlines. You can learn at your own pace.")
    ],
    "Certificates": [
        ("Do I get a certificate?", "Yes, a Certificate of Completion is generated when you finish all course content."),
        ("Is the certificate accredited?", "Our certificates show you completed the training, but they are not university degrees."),
        ("How do I download my certificate?", "When you finish the course, a trophy icon will appear. Click it to download your certificate."),
        ("Can I add it to LinkedIn?", "Yes, there is a distinct 'Add to Profile' button for LinkedIn on your certificate page."),
        ("My name is wrong on the certificate", "You can update your profile name in settings, and the certificate will automatically update.")
    ],
    "Troubleshooting": [
        ("The video is buffering", "Try lowering the video quality or checking your internet connection."),
        ("There is no sound", "Check if the player is muted or if your device volume is up. Try a different browser."),
        ("The screen is black", "Try refreshing the page, clearing your cache, or disabling browser extensions."),
        ("I can't access my course", "Ensure you are logged into the correct account used for purchase."),
        ("The app is crashing", "Try reinstalling the app or checking for updates in the App Store/Play Store.")
    ],
    "Instructor Interaction": [
        ("Can I ask the teacher questions?", "Yes, use the Q&A section in the course player to ask questions."),
        ("How do I rate a course?", "You will be prompted to leave a rating after watching a few lectures, or you can do it from the dashboard."),
        ("Can I message the instructor directly?", "Direct messaging depends on the instructor's settings, but Q&A is the best place for course questions."),
        ("Who are the instructors?", "They are experts in their fields. You can read their bio on the course landing page.")
    ],
    "Chit-Chat / Social": [
        ("Hello", "Hi there! Ready to learn something new today?"),
        ("Hi", "Hello! How can I help you?"),
        ("Good morning", "Good morning! What course are you looking for?"),
        ("Thank you", "You're welcome! Happy learning."),
        ("Bye", "Goodbye! Come back soon."),
        ("Who are you?", "I am the course assistant chatbot."),
        ("What can you do?", "I can help you find courses, answer account questions, and explain platform features."),
        ("You are helpful", "Thank you! I try my best."),
        ("I am bored", "Why not learn a new skill? Ask me for course recommendations!"),
        ("Tell me a joke", "Why do programmers prefer dark mode? Because light attracts bugs!")
    ]
}

# Add expanded questions to the main list
for category, qa_list in general_qa_categories.items():
    for q, a in qa_list:
        questions.append(q)
        answers.append(a)

# Create DataFrame
final_df = pd.DataFrame({'question': questions, 'answer': answers})

# Save
final_df.to_excel('chatbot_dataset.xlsx', index=False)

print(f"Total rows: {len(final_df)}")
print(final_df.tail(10))