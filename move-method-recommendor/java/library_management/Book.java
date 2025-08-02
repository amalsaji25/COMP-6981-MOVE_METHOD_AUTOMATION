package java.library_management;

public class Book {
    private String title;
    private String author;
    private boolean isAvailable = true;

    public Book(String title, String author) {
        this.title = title;
        this.author = author;
    }

    public void borrow() {
        if (isAvailable) {
            isAvailable = false;
        } else {
            throw new IllegalStateException("Book is already borrowed");
        }
    }

    public void returnBook() {
        isAvailable = true;
    }

    public boolean isAvailable() {
        return isAvailable;
    }

    public String getTitle() {
        return title;
    }

    public String getAuthor() {
        return author;
    }
}
