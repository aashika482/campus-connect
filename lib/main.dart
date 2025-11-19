import 'package:flutter/material.dart';
import 'screens/main_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'College Club App',
      theme: ThemeData.dark().copyWith(
        primaryColor: const Color(0xFF8A2BE2), // A shade of purple
        scaffoldBackgroundColor: const Color(0xFF121212), // Dark background
        hintColor: const Color(0xFF8A2BE2),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Colors.black26,
          selectedItemColor: Color(0xFF9B59B6),
          unselectedItemColor: Colors.grey,
          type: BottomNavigationBarType.fixed,
        ),
      ),
      debugShowCheckedModeBanner: false,
      home: const MainScreen(),
    );
  }
}