package java.library_management;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class Library {
    private Map<String, Book> catalog         = new HashMap<>();  
    private Map<User, List<Book>> userLoans   = new HashMap<>();

    public void addBookToLibrary(Book book) {
        catalog.put(book.getISBN(), book);
    }

    public void recordBorrowedBook(User user, Book book) {
        userLoans.computeIfAbsent(user, k -> new ArrayList<>()).add(book);
    }

    public boolean removeBorrowedBook(User user, Book book) {
        if (userLoans.containsKey(user)) {
            return userLoans.get(user).remove(book);
        }
        return false;
    }

    public List<Book> searchABookInLibrary(String query) {
        List<Book> matches = new ArrayList<>();
        for (Book b : catalog.values()) {
            if (b.getTitle().contains(query) ||
                b.getAuthor().contains(query) ||
                b.getISBN().equals(query)) {
                matches.add(b);
            }
        }
        return matches;
    }

    public List<Book> getAvailableBooksInLibrary() {
        List<Book> available = new ArrayList<>();
        for (Book b : catalog.values()) {
            if (b.isAvailable()) available.add(b);
        }
        return available;
    }

    public List<Book> getInventory() {
        return new ArrayList<>(catalog.values());
    }

    public Map<User, List<Book>> getUserLoans() {
        return userLoans;
    }

    public String formatUserProfile(User user) {
        StringBuilder sb = new StringBuilder();
        sb.append("User: ").append(user.getUserName())
          .append(" (").append(user.getEmail()).append(")\n")
          .append("Borrowed books:\n");
        for (Book b : userLoans.getOrDefault(user, List.of())) {
            sb.append(" • ").append(b.getTitle())
              .append(" due ").append(b.getDueDate()).append("\n");
        }
        return sb.toString();
    }

    public String generateUserLoanReport(User user) {
        StringBuilder report = new StringBuilder();
        report.append("Loan Report for ").append(user.getUserId()).append("\n");
        for (Book b : userLoans.getOrDefault(user, List.of())) {
            report.append(b.getTitle())
                  .append(" by ").append(b.getAuthor())
                  .append(" — due ").append(b.getDueDate())
                  .append("\n");
        }
        return report.toString();
    }

    public Map<String, Integer> calculateBookUtilizationStats() {
        Map<String, Integer> stats = new HashMap<>();
        for (Book b : catalog.values()) {
            int count = 0;
            for (List<Book> loans : userLoans.values()) {
                for (Book loaned : loans) {
                    if (loaned.getISBN().equals(b.getISBN())) {
                        count++;
                    }
                }
            }
            stats.put(b.getTitle(), count);
        }
        return stats;
    }

    public double calculateFine(User user, Date today) {
        double total = 0;
        for (Book b : userLoans.getOrDefault(user, List.of())) {
            long daysLate = java.time.temporal.ChronoUnit.DAYS.between(
                b.getDueDate().toInstant(), today.toInstant()
            );
            if (daysLate > 0) {
                total += daysLate * 1.0; 
            }
        }
        return total;
    }
}