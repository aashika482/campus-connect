import 'package:flutter/material.dart'; 

class SavedPage extends StatelessWidget {
  const SavedPage({super.key});
  
  //list of saved event images
  final List<String> savedEventImages = const [
    'assets/images/saved1.png',
    'assets/images/saved2.png',
    'assets/images/saved3.png',
    'assets/images/saved4.jpg',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Saved'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(8.0),
        child: GridView.builder(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 10.0,
            mainAxisSpacing: 10.0,
            childAspectRatio: 0.7, // Adjust if images look stretched
          ),
          itemCount: savedEventImages.length,
          itemBuilder: (context, index) {
            return ClipRRect(
              borderRadius: BorderRadius.circular(12.0),
              child: Image.asset(savedEventImages[index], fit: BoxFit.cover),
            );
          },
        ),
      ),
    );
  }
}