import { Component } from "@angular/core";
import { FreePark } from "../models";
import { SearchService } from "../services";
import { Subscription } from "rxjs/Subscription";

@Component({
    selector: 'free-parks',
    providers: [],
    styleUrls: ['./freeparks.component.css'],
    templateUrl: './freeparks.component.html'
})
export class FreeParksComponent {

    private freeParks: FreePark[] = [];
    private subscription: Subscription;
    // Stores the currently ordered field and direction (ascending or descending)
    private order = {fieldName: 'parkName', direction: 'desc'};

    constructor(private searchService: SearchService) {
        this.subscription = this.searchService.subscribeFreeParks(
            (freeParks) => this.freeParks = freeParks
        );
    }

    public orderBy(fieldName: string) {
        let direction = this.order.direction;

        if (fieldName === this.order.fieldName) {
            // If the field name is the same as last time, then we're switching direction.
            direction = 'desc' === direction ? 'asc' : 'desc';
        } else {
            // If the field name is different then default to descending first.
            direction = 'desc';
        }
        // Save the new order
        this.order.fieldName = fieldName;
        this.order.direction = direction;

        // Sort the list of parks
        this.freeParks.sort((n1, n2) => {
            if (n1[fieldName] > n2[fieldName]) {
                return direction === 'desc' ? 1 : -1;
            }
            if (n1[fieldName] < n2[fieldName]) {
                return direction === 'desc' ? -1 : 1;
            }
            return 0;
        });
    }
}
