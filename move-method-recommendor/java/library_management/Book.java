package java.library_management;

public class Book {
    private String title;
    private String author;
    private String isbn;
    private boolean isAvailable;
    private java.util.Date dueDate;

    public Book(String title, String author, String isbn) {
        this.title       = title;
        this.author      = author;
        this.isbn        = isbn;
        this.isAvailable = true;
    }

    public String getTitle()     { return title; }
    public String getAuthor()    { return author; }
    public String getISBN()      { return isbn; }
    public boolean isAvailable() { return isAvailable; }
    public java.util.Date getDueDate() { return dueDate; }

    public void borrow(java.util.Date dueDate) {
        this.isAvailable = false;
        this.dueDate     = dueDate;
    }

    public void returnBook() {
        this.isAvailable = true;
        this.dueDate     = null;
    }
}