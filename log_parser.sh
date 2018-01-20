#!/bin/bash
grep -o "Bought.*\|Sold.*" Force.log > buffer.log
cat buffer.log | awk '\
BEGIN\
    {   counter = 1;
        buy_time = -1;
        buy_price = -1;
        sell_time = -1;
        sell_price = -1;
        output = 0;
    }

    {
        # counter shows 1 for odd lines and 0 for even lines
        counter = counter % 2

        # odd lines == BUY line
        if (counter == 1)
        {
            buy_time = $NF;
            buy_price = substr($4, 3);
            output = 0;
        }
        # even lines == SELL line
        else if (counter == 0)
        {
            sell_time = $NF;
            sell_price = substr($4, 3);
            output = 1;
        }
        # Increment counter

        counter = counter + 1;
    }
    {
        if (output == 1){
            if (sell_price < buy_price)
                print (buy_time, sell_time, -1);
            elif (buy_price < sell_price)
                print (buy_time, sell_time, 1);
        }
    }
\'