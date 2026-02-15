// lib/data_model.dart
class Event {
  final String imagePath;
  final String title;
  final String organizer;
  final List<String> tags;

  Event(
      {required this.imagePath,
      required this.title,
      required this.organizer,
      required this.tags});
}
String userName = "User"; 
// Global variable for user interests
List<String> userInterests = [];

//Catalog of Events
final List<Event> allEventsData = [
  Event(
    imagePath: 'assets/images/event1.jpg',
    title: 'MUJ HACKX 3.0',
    organizer: 'E-Cell X AIC MUJ',
    tags: ['Tech', 'Coding', 'Hackathon'],
  ),
  Event(
    imagePath: 'assets/images/event2.jpg',
    title: 'Indian Ocean Live',
    organizer: 'TMC: The Music Club',
    tags: ['Music', 'Concert'],
  ),
  Event(
    imagePath: 'assets/images/event3.png',
    title: 'Rewind and Recode',
    organizer: 'Cyber Space: The Coding Club',
    tags: ['Tech', 'Coding'],
  ),
  Event(
    imagePath: 'assets/images/event4.png',
    title: 'Breached 5.0',
    organizer: 'IEEE Computer Society',
    tags: ['Tech', 'Cryptic Hunt'],
  ),
  Event(
    imagePath: 'assets/images/event5.png',
    title: 'Pirates of the Code',
    organizer: 'The Cypher Club',
    tags: ['Coding', 'Treasure Hunt'],
  ),
  Event(
    imagePath: 'assets/images/event6.png',
    title: 'Hymns of Joy',
    organizer: 'Humans of MUJ',
    tags: ['Art', 'Photography', 'Culture'],
  ),
];

// Logic to get recommendations
List<Event> getForYouEvents() {
  if (userInterests.isEmpty) {
    // If nothing selected, show the first few events as default
    return allEventsData;
  }

  // Filter events: Keep event IF it has a tag that matches userInterests
  return allEventsData.where((event) {
    return event.tags.any((tag) => userInterests.contains(tag));
  }).toList();
}
