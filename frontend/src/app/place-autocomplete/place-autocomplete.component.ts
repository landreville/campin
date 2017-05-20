/**
 * Autocomplete input field for Google places.
 *
 * Requires google maps script in html page. Example:
 * <script src="https://maps.googleapis.com/maps/api/js?key=your_key&libraries=places">
 * </script>
 */
import {
    Component,
    EventEmitter,
    forwardRef,
    OnInit,
    Output,
    ViewChild
} from "@angular/core";
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from "@angular/forms";

// Get the google Javascript global.
declare let google;

interface GeocoderAddressComponent {
    long_name: string;
    short_name: string;
    types: {
        [index: number]: string;
    };
}

interface PlaceGeometry {
    location: {
        lat: number;
        lng: number;
    };

}

/**
 * Interface for values emitted from the PlaceAutocompleteComponent.
 */
export interface PlaceResult {
    address_components: {
        [index: number]: GeocoderAddressComponent;
    };
    formatted_address: string;
    geometry: PlaceGeometry;
    name: string;
    place_id: string;
    types: {
        [index: number]: string;
    };
    url: string;
    vicinity: string;
}

/**
 * Autocomplete input field for Google places.
 *
 * This will provide an autocomplete drop-down of city names. When a city
 * is chosen an onPlaceChosen event will be emitted with a PlaceResult object.
 *
 * This component also implements the ControlValueAccessor which allows it to be
 * used in ngModel based forms.
 */
@Component({
    selector: 'place-autocomplete',
    templateUrl: './place-autocomplete.component.html',
    styleUrls: ['./place-autocomplete.component.css'],
    providers: [
        {
            provide: NG_VALUE_ACCESSOR,
            useExisting: forwardRef(() => PlaceAutocompleteComponent),
            multi: true
        }
    ]
})
export class PlaceAutocompleteComponent implements OnInit, ControlValueAccessor {

    @Output() public onPlaceChosen = new EventEmitter<PlaceResult>();
    private innerValue: PlaceResult = null;
    @ViewChild('placesAutocomplete') private placesAutocomplete;

    public ngOnInit() {
        let autocomplete = new google.maps.places.Autocomplete(
            this.placesAutocomplete.nativeElement,
            {
                types: ['(cities)'],
                componentRestrictions: {country: 'CA'}
            }
        );

        autocomplete.addListener(
            'place_changed',
            () => this.placeChosen(autocomplete)
        );
    }

    public writeValue(value: PlaceResult) {
        if (value !== this.innerValue) {
            this.innerValue = value;
        }
    }

    public registerOnChange(fn: (_: any) => void) {
        this.onChangeCallback = fn;
    }

    public registerOnTouched(fn: () => void) {
        this.onTouchedCallback = fn;
    }

    private onTouchedCallback: () => void = () => undefined;
    private onChangeCallback: (_: any) => void = () => undefined;

    private placeChosen(autocomplete) {
        let place: PlaceResult = autocomplete.getPlace();
        this.onPlaceChosen.emit(place);
        this.onChangeCallback(place);
    }
}
