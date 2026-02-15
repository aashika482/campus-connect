import 'package:flutter/material.dart';
import 'screens/login_page.dart'; // Import the login page

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
        primaryColor: const Color(0xFF8A2BE2),
        scaffoldBackgroundColor: const Color(0xFF121212),
        hintColor: const Color(0xFF8A2BE2),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Colors.black26,
          selectedItemColor: Color(0xFF9B59B6),
          unselectedItemColor: Colors.grey,
          type: BottomNavigationBarType.fixed,
        ),
      ),
      debugShowCheckedModeBanner: false,
      home: const LoginPage(), 
    );
  }
}