public class BinarySearch {

    public static int search(int[] arr, int x) {
        int low = 0;
        int high = arr.length - 1;
        while (low <= high) {
            int mid = low + (high - low) / 2;
            int v = arr[mid];
            if (v == x) return mid;
            if (v < x) low = mid + 1;
            else high = mid - 1;
        }
        return -1;
    }
}