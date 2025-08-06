package java.library_management;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;

public class User {
    private String userName;
    private String userId;
    private String email;
    private Library library;

    public User(String userName, String userId, String email, Library library) {
        this.userName    = userName;
        this.userId  = userId;
        this.email   = email;
        this.library = library;
    }


    public void borrowBook(Book book, Date dueDate) {
        if (book.isAvailable()) {
            book.borrow(dueDate);
            library.recordBorrowedBook(this, book);
        }
    }

    public void returnBook(Book book) {
        if (library.removeBorrowedBook(this, book)) {
            book.returnBook();
        }
    }


    public List<Book> searchCatalog(String query) {
        return library.searchABookInLibrary(query);
    }

    public List<Book> viewAvailableBooks() {
        List<Book> available = new ArrayList<>();
        for (Book b : library.getInventory()) {
            if (b.isAvailable()) {
                available.add(b);
            }
        }
        return available;
    }

    public List<Book> getOverdueBooks(Date today) {
        List<Book> overdue = new ArrayList<>();
        Map<User, List<Book>> loans = library.getUserLoans();
        for (Book b : loans.getOrDefault(this, List.of())) {
            if (b.getDueDate().before(today)) {
                overdue.add(b);
            }
        }
        return overdue;
    }

    public double calculateOutstandingFines(Date today) {
        return library.calculateFine(this, today);
    }

    public void notifyOverdueReminders(Date today) {
        List<Book> overdue = getOverdueBooks(today);
        for (Book b : overdue) {
            System.out.println(
                "Email to " + email +
                ": you have an overdue book \"" + b.getTitle() + "\""
            );
        }
    }

    public String getUserName()   { return userName; }
    public String getUserId() { return userId; }
    public String getEmail()  { return email; }
}