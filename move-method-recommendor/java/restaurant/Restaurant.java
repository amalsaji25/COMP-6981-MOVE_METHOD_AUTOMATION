package java.restaurant;

import java.util.*;

public class Restaurant {
    private final MenuRepository menuRepo = new MenuRepository();
    private final OrderRepository orderRepo = new OrderRepository();

    public void addMenuItem(MenuItem item) {
        menuRepo.add(item);
    }

    public void removeMenuItem(MenuItem item) {
        menuRepo.remove(item);
    }

    public MenuItem findMenuItem(String name) {
        return menuRepo.findByName(name);
    }

    public Order placeOrder(Customer customer, List<MenuItem> items) {
        Order o = new Order(customer, items);
        orderRepo.save(o);
        NotificationService.notify(customer, "Your order has been placed.");
        return o;
    }

    public boolean cancelOrder(Order o) {
        boolean removed = orderRepo.delete(o);
        if (removed) {
            NotificationService.notify(o.getCustomer(), "Your order has been cancelled.");
        }
        return removed;
    }

    public void loadMenu() {
        menuRepo.loadAll();
    }

    public void saveMenu() {
        menuRepo.saveAll();
    }

    public String generateDailyReport() {
        ReportService rs = new ReportService();
        return rs.compileDailySales(orderRepo.findAll());
    }
}
