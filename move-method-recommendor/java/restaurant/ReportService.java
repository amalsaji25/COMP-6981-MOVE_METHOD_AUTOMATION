package java.restaurant;

import java.util.List;

public class ReportService {
    public String compileDailySales(List<Order> orders) {
        double total = orders.stream()
            .mapToDouble(Order::getTotal)
            .sum();
        int count = orders.size();
        return "Daily Sales: " + count + " orders, Total revenue: $" + total;
    }
}
