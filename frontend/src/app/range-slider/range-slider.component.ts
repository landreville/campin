import { Component, EventEmitter, Input, Output } from "@angular/core";

/**
 * Range slider that returns string values instead of numeric values.
 *
 * An onLabelClick event is emitted with the chosen value. Note that this
 * component is not implemented to be used with ngModel based forms.
 */
@Component({
    selector: 'range-slider',
    providers: [],
    styleUrls: ['./range-slider.component.css'],
    templateUrl: './range-slider.component.html'
})
export class RangeSliderComponent {
    public value: number = 0;
    public min: number = 0;
    @Input() public labels: string[];
    @Output() public rangeSelected: EventEmitter<string> = new EventEmitter();

    public get max() {
        return this.labels.length - 1;
    }

    public onChange(event) {
        let i = parseInt(event.target.value);
        let labelValue = this.labels[i];
        this.rangeSelected.emit(labelValue);
    }

    public onLabelClick(value) {
        this.value = value;
    }
}
