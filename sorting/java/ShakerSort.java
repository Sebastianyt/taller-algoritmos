// Java program for implementation of Cocktail Sort
public class ShakerSort {
    public static class ShakerSortTimeout extends RuntimeException {
        public ShakerSortTimeout(String message) {
            super(message);
        }
    }

    public void cocktailSort(int[] a) {
        cocktailSort(a, 0L);
    }

    /**
     * @param timeoutMillis 0 para sin timeout; >0 para limite de tiempo.
     */
    public void cocktailSort(int[] a, long timeoutMillis) {
        final long startNs = System.nanoTime();
        final long timeoutNs = timeoutMillis > 0 ? timeoutMillis * 1_000_000L : 0L;

        Runnable checkTimeout = () -> {
            if (timeoutNs > 0) {
                long elapsed = System.nanoTime() - startNs;
                if (elapsed >= timeoutNs) {
                    throw new ShakerSortTimeout("Shaker Sort timeout after " + timeoutMillis + " ms");
                }
            }
        };

        boolean swapped = true;
        int start = 0;
        int end = a.length;

        while (swapped == true) 
        {
            checkTimeout.run();
            // reset the swapped flag on entering the
            // loop, because it might be true from a
            // previous iteration.
            swapped = false;

            // loop from bottom to top same as
            // the bubble sort
            for (int i = start; i < end - 1; ++i) 
            {
                if (a[i] > a[i + 1]) {
                    int temp = a[i];
                    a[i] = a[i + 1];
                    a[i + 1] = temp;
                    swapped = true;
                }
            }

            // if nothing moved, then array is sorted.
            if (swapped == false)
                break;

            // otherwise, reset the swapped flag so that it
            // can be used in the next stage
            swapped = false;

            // move the end point back by one, because
            // item at the end is in its rightful spot
            end = end - 1;

            // from top to bottom, doing the
            // same comparison as in the previous stage
            checkTimeout.run();
            for (int i = end - 1; i >= start; i--) 
            {
                if (a[i] > a[i + 1]) 
                {
                    int temp = a[i];
                    a[i] = a[i + 1];
                    a[i + 1] = temp;
                    swapped = true;
                }
            }

            // increase the starting point, because
            // the last stage would have moved the next
            // smallest number to its rightful spot.
            start = start + 1;
        }
    }

}