package java.restaurant;

public class NotificationService {
    public static void notify(Customer c, String msg) {
        System.out.println("Notify " + c.getContact() + ": " + msg);
    }
}
