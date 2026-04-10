public class TernarySearch {

    public static int search(int[] arr, int x) {
        int low = 0;
        int high = arr.length - 1;

        while (low <= high) {
            int third = (high - low) / 3;
            int mid1 = low + third;
            int mid2 = high - third;

            int v1 = arr[mid1];
            int v2 = arr[mid2];
            if (v1 == x) return mid1;
            if (v2 == x) return mid2;

            if (x < v1) high = mid1 - 1;
            else if (x > v2) low = mid2 + 1;
            else {
                low = mid1 + 1;
                high = mid2 - 1;
            }
        }
        return -1;
    }
}