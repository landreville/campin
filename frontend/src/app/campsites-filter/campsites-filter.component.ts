import { Component, EventEmitter, Output } from "@angular/core";
import { RangeSliderComponent } from "../range-slider";

/**
  Component to display filter form for campsites.

  Use the filterSelected event to listen for filter changes. The filter values
  will be either poor, average, or good.

  Filter events are emitted with both filter values even if only one changed.
  The filter event looks like: { privacy: 'Poor', quality: 'Good' }
 */
@Component({
    selector: 'campsites-filter',
    providers: [RangeSliderComponent],
    styleUrls: ['./campsites-filter.component.css'],
    templateUrl: './campsites-filter.component.html'
})
export class CampSitesFilterComponent {
    @Output() public filterSelected: EventEmitter<any> = new EventEmitter();
    private filter = {privacy: 'Poor', quality: 'Poor'};

    public onChange(value, field) {
        this.filter[field] = value;
        this.filterSelected.emit(this.filter);
    }
}
