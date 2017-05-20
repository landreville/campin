import { Component, Inject } from "@angular/core";
import { DOCUMENT } from "@angular/platform-browser";
import { IMyOptions } from "mydatepicker";
import { PlaceAutocompleteComponent } from "../place-autocomplete";
import { Search } from "../models";
import { SearchService } from "../services";
import { Router } from "@angular/router";
import { PageScrollInstance, PageScrollService } from "ng2-page-scroll";

@Component({
    selector: 'search',
    providers: [PlaceAutocompleteComponent],
    styleUrls: ['./search.component.css'],
    templateUrl: './search.component.html'
})
export class SearchComponent {

    public myDatePickerOptions: IMyOptions = {
        openSelectorOnInputClick: true,
        dateFormat: 'yyyy-mm-dd',
        firstDayOfWeek: 'su',
        height: '1.5rem'
    };

    // Model will be updated as form inputs are changed using ngModel
    public model = new Search(undefined, undefined, 0, undefined);
    public submitted = false;
    // Used to disable the submit button while the form is submitting.
    public submitting = false;

    constructor(private searchService: SearchService,
                private router: Router,
                private pageScrollService: PageScrollService,
                @Inject(DOCUMENT) private document: any) {
    }

    public onSubmit(event) {
        event.preventDefault();
        if (!this.model) {
            return;
        }
        this.submitted = true;
        // Mark submitting to disable submit button.
        this.submitting = true;
        this.clearResults();
        this.searchService.searchFreeParks(this.model)
            .subscribe(
                (freeParks) => {
                    // Re-enables submit button.
                    this.submitting = false;
                    // Router outlet is below search form.
                    this.router.navigate(['parks/free']);
                    // Scroll to router outlet
                    let pageScrollInstance: PageScrollInstance = PageScrollInstance.simpleInstance(
                        this.document, '#search-results'
                    );
                    this.pageScrollService.start(pageScrollInstance);
                    return freeParks;
                },
                (error) => {
                    // Re-enables submit button.
                    this.submitting = false;
                    throw error;
                }
            );
    }

    public clearResults() {
        this.router.navigate(['']);
        this.searchService.clearFreeParks();
    }
}
