# CampusConnect: College Club Discovery App 🚀

**CampusConnect** is a centralized mobile platform designed to bridge the communication gap between college student clubs and the student body. Built with **Flutter**, it provides a one-stop solution for students to discover events, manage club memberships, and personalize their extracurricular experience.

---

## 📱 Features

- **Personalized Onboarding**: Users enter their name and select specific interests (Tech, Music, Art, etc.) to tailor their experience.
- **Smart Recommendation Engine**: A "For You" section that uses tag-based logic to suggest events matching the user's selected interests.
- **Event Discovery**: Browse upcoming college events with detailed information and high-quality visual banners.
- **Club Directory**: A comprehensive list of all registered campus clubs and their details.
- **Event Bookmarking**: Save events of interest for quick access later (MVP UI implemented).
- **Modern UI/UX**: Designed following Material Design principles with a sleek "Dark Mode" aesthetic.

---

## 🛠️ Technology Stack (This is still a Frontend Protype)

- **Frontend**: Flutter (UI Software Development Kit)
- **Language**: Dart
- **State Management**: Local Global State (Scalable to Provider/Bloc)
- **Backend (Planned)**: Google Firebase (Authentication, Cloud Firestore, Cloud Storage)
- **Version Control**: Git & GitHub

---

## 📂 Project Structure


lib/
├── screens/
│   ├── login_page.dart           # User onboarding & name entry
│   ├── interest_selection_page.dart # Tag-based interest selection
│   ├── main_screen.dart         # Bottom navigation controller
│   ├── home_page.dart           # Personalized dashboard with recommendations
│   ├── all_events_page.dart     # Full list of campus events
│   ├── all_clubs_page.dart      # Directory of campus clubs
│   └── saved_page.dart          # Bookmarked events view
├── data_model.dart              # Global state, Event classes, and Recommendation logic
└── main.dart                    # App entry point and Theme configuration

#🗺️ Roadmap (Future Enhancements)

The project is designed to be easily upgraded to a full-stack application. Future updates will include:

-Firebase Authentication: Replacing the simple name entry with secure Google/Email login.
-Cloud Firestore: Migrating the allEventsData catalog from a local file to a real-time database.
-Cloud Storage: Hosting event posters and club logos online to reduce the app's installation size.
-Push Notifications: Real-time alerts for new events in categories the user has selected.

```text


